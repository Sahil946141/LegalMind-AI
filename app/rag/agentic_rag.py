# app/rag/agentic_qna.py
import os
import re
import time
import uuid
import logging
from typing import Any

from google import genai
from groq import Groq
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

from app.db.connection import (
    get_document,
    insert_qna_log,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agentic_qna")

# ---------------- CONFIG ----------------
ST_MODEL_NAME = os.getenv("ST_MODEL_NAME", "all-MiniLM-L6-v2")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# Primary provider: Gemini
GEMINI_REWRITE_MODEL = os.getenv("GEMINI_REWRITE_MODEL", "gemini-2.5-flash")
GEMINI_ANSWER_MODEL = os.getenv("GEMINI_ANSWER_MODEL", "gemini-2.5-flash")

# Fallback provider: Groq
GROQ_REWRITE_MODEL = os.getenv("GROQ_REWRITE_MODEL", "gemma2-9b-it")
GROQ_ANSWER_MODEL = os.getenv("GROQ_ANSWER_MODEL", "qwen/qwen3-32b")

TOP_K_INITIAL = 10
TOP_K_RETRY = 10
MAX_CONTEXT_CHARS = 12000

# Loosened slightly from earlier
BEST_SCORE_STRONG = float(os.getenv("BEST_SCORE_STRONG", "0.45"))
BEST_SCORE_MIN = float(os.getenv("BEST_SCORE_MIN", "0.30"))

MAX_REWRITE_BUDGET_MS = 2500

# ---------------- CLIENTS ----------------
embedder = SentenceTransformer(ST_MODEL_NAME)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------- HELPERS ----------------
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def embed_query(text: str):
    return embedder.encode([text], normalize_embeddings=True)[0].tolist()


def _match_get(match: Any, key: str, default=None):
    if isinstance(match, dict):
        return match.get(key, default)
    return getattr(match, key, default)


def pinecone_query(user_id: str, doc_id: str, query: str, top_k: int):
    qvec = embed_query(query)

    res = index.query(
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
        filter={
            "user_id": user_id,
            "doc_id": doc_id,
        },
    )

    if isinstance(res, dict):
        return res.get("matches", [])

    return res.matches or []


def build_context(matches):
    blocks = []
    citations = []
    total_chars = 0

    for match in matches:
        metadata = _match_get(match, "metadata", {}) or {}
        text = normalize_text(metadata.get("text", ""))

        if not text:
            continue

        filename = metadata.get("filename")
        page = metadata.get("page")
        chunk_index = metadata.get("chunk_index")
        score = float(_match_get(match, "score", 0.0) or 0.0)

        block = f"[source: {filename} | page: {page} | chunk: {chunk_index}]\n{text}"

        if total_chars + len(block) > MAX_CONTEXT_CHARS:
            break

        blocks.append(block)
        citations.append(
            {
                "filename": filename,
                "page": page,
                "chunk_index": chunk_index,
                "score": score,
            }
        )
        total_chars += len(block)

    best_score = citations[0]["score"] if citations else 0.0
    return "\n\n---\n\n".join(blocks), citations, best_score


def has_strong_evidence(best_score: float, citations: list) -> bool:
    return best_score >= BEST_SCORE_STRONG and len(citations) >= 2


def has_minimum_evidence(best_score: float, citations: list) -> bool:
    return best_score >= BEST_SCORE_MIN and len(citations) >= 1


def has_any_evidence(citations: list) -> bool:
    return len(citations) > 0


def get_confidence_level(best_score: float, citations: list) -> str:
    if not citations:
        return "none"
    if best_score >= BEST_SCORE_STRONG and len(citations) >= 2:
        return "high"
    if best_score >= BEST_SCORE_MIN and len(citations) >= 1:
        return "medium"
    return "low"


def is_complex_question(question: str) -> bool:
    q = question.lower()

    complex_terms = [
        "risk",
        "liable",
        "liability",
        "indemnity",
        "breach",
        "compare",
        "conflict",
        "implication",
        "termination",
        "penalty",
        "damages",
        "obligation",
        "consequence",
        "what happens if",
    ]

    return any(term in q for term in complex_terms)


def extractive_fallback_answer(question: str, context: str) -> str:
    """
    Local safety fallback when both LLM providers fail.
    Returns a short extractive answer from the first relevant sentence(s).
    """
    if not context:
        return "Not found in context."

    cleaned = re.sub(r"\[source:.*?\]\n", "", context)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    q = question.lower()
    keyword_groups = [
        ["party", "parties", "between", "company", "distributor"],
        ["product", "sell", "energy saver", "device"],
        ["exclusive", "market", "illinois"],
        ["term", "duration", "years", "year"],
        ["payment", "pay", "days", "receipt"],
        ["law", "governing", "illinois"],
        ["terminate", "termination", "notice", "immediately", "insolvent", "bankruptcy"],
        ["name", "license", "termination"],
    ]

    scored = []
    for sent in sentences:
        s = sent.strip()
        if not s:
            continue

        score = 0
        q_words = set(re.findall(r"\w+", q))
        s_words = set(re.findall(r"\w+", s.lower()))

        score += len(q_words.intersection(s_words))

        for group in keyword_groups:
            if any(word in q for word in group):
                score += sum(1 for word in group if word in s.lower())

        if score > 0:
            scored.append((score, s))

    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        best_sentences = [scored[0][1]]

        if len(scored) > 1 and scored[1][0] >= max(1, scored[0][0] - 1):
            best_sentences.append(scored[1][1])

        answer = " ".join(best_sentences).strip()
        return answer[:700]

    first_chunk = cleaned.strip()[:500]
    return first_chunk if first_chunk else "Not found in context."


def _log_and_return(
    *,
    qna_id: str,
    user_id: str,
    doc_id: str,
    question: str,
    answer: str,
    rewrite_used: bool,
    used_model: str,
    best_score: float,
    latency_ms: int,
    citations: list,
    status: str,
    confidence: str,
):
    insert_qna_log(
        qna_id=qna_id,
        user_id=user_id,
        doc_id=doc_id,
        question=question,
        answer=answer,
        mode="agentic",
        rewrite_used=rewrite_used,
        used_model=used_model,
        best_score=best_score,
        latency_ms=latency_ms,
        citations_json=citations,
        status=status,
    )

    return {
        "qna_id": qna_id,
        "mode": "agentic",
        "answer": answer,
        "citations": citations,
        "rewrite_used": rewrite_used,
        "used_model": used_model,
        "best_score": best_score,
        "latency_ms": latency_ms,
        "status": status,
        "confidence": confidence,
    }


# ---------------- MODEL CALLS ----------------
def gemini_generate(model: str, prompt: str) -> str:
    resp = gemini_client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return normalize_text(getattr(resp, "text", "") or "")


def groq_generate(model: str, prompt: str, max_tokens: int = 700) -> str:
    resp = groq_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
    )
    content = resp.choices[0].message.content
    return normalize_text(content or "")


def rewrite_query_with_gemini(question: str) -> str:
    prompt = f"""
Rewrite this question into a short legal search query.
Return only one line.
Do not add explanation.

Question:
{question}
""".strip()

    return gemini_generate(GEMINI_REWRITE_MODEL, prompt) or question


def rewrite_query_with_groq(question: str) -> str:
    prompt = f"""
Rewrite this question into a short legal search query.
Return only one line.
Do not add explanation.

Question:
{question}
""".strip()

    return groq_generate(GROQ_REWRITE_MODEL, prompt, max_tokens=100) or question


def rewrite_query(question: str) -> tuple[str, str]:
    try:
        log.info(f"[REWRITE] Trying Gemini model={GEMINI_REWRITE_MODEL}")
        rewritten = rewrite_query_with_gemini(question)
        return rewritten, GEMINI_REWRITE_MODEL

    except Exception as gemini_error:
        log.warning(
            f"[GEMINI REWRITE FAILED] model={GEMINI_REWRITE_MODEL} error={gemini_error}"
        )

        try:
            log.info(f"[REWRITE] Falling back to Groq model={GROQ_REWRITE_MODEL}")
            rewritten = rewrite_query_with_groq(question)
            return rewritten, GROQ_REWRITE_MODEL

        except Exception as groq_error:
            log.error(
                f"[GROQ REWRITE FAILED] model={GROQ_REWRITE_MODEL} error={groq_error}"
            )
            raise RuntimeError("Both Gemini and Groq rewrite failed")


def answer_with_gemini(
    question: str,
    context: str,
    complex_question: bool,
    confidence: str,
) -> str:
    extra_parts = []

    if complex_question:
        extra_parts.append(
            "If relevant, explain implications, risks, and obligations in simple legal language."
        )

    if confidence == "low":
        extra_parts.append(
            "The retrieved context may be incomplete. "
            "Answer cautiously using only the context."
        )

    extra = " ".join(extra_parts)

    prompt = f"""
You are a legal assistant answering questions about a contract.

Use ONLY the provided context.

Rules:
- Answer exactly what is asked
- Be concise (1-2 sentences)
- Do NOT include unrelated clauses or extra obligations
- Do NOT add external knowledge
- If the answer is not present in the context, say: "Not found in context"

Guidelines:
- "Who" → return exact names from the contract
- "What is" → give a direct clause or definition
- "Is/Does" → answer Yes or No, then a short explanation
- "How/Why" → explain briefly using only relevant lines

{extra}

Question:
{question}

Context:
{context}
""".strip()

    return gemini_generate(GEMINI_ANSWER_MODEL, prompt)


def answer_with_groq(
    question: str,
    context: str,
    complex_question: bool,
    confidence: str,
) -> str:
    extra_parts = []

    if complex_question:
        extra_parts.append(
            "If relevant, explain implications, risks, and obligations in simple legal language."
        )

    if confidence == "low":
        extra_parts.append(
            "The retrieved context may be incomplete. "
            "Answer cautiously using only the context."
        )

    extra = " ".join(extra_parts)

    prompt = f"""
You are a legal assistant answering questions about a contract.

Use ONLY the provided context.

Rules:
- Answer exactly what is asked
- Be concise
- Do NOT include unrelated clauses or extra information
- Do NOT add external knowledge
- If the answer is not present in the context, say: "Not found in context"

{extra}

Question:
{question}

Context:
{context}
""".strip()

    return groq_generate(GROQ_ANSWER_MODEL, prompt, max_tokens=500)


def answer_with_selected_provider(
    question: str,
    context: str,
    complex_question: bool,
    confidence: str,
) -> tuple[str, str]:
    try:
        log.info(f"[ANSWER] Trying Gemini model={GEMINI_ANSWER_MODEL}")

        answer = answer_with_gemini(
            question=question,
            context=context,
            complex_question=complex_question,
            confidence=confidence,
        )
        return answer, GEMINI_ANSWER_MODEL

    except Exception as gemini_error:
        log.warning(
            f"[GEMINI ANSWER FAILED] model={GEMINI_ANSWER_MODEL} error={gemini_error}"
        )

        try:
            log.info(f"[ANSWER] Falling back to Groq model={GROQ_ANSWER_MODEL}")

            answer = answer_with_groq(
                question=question,
                context=context,
                complex_question=complex_question,
                confidence=confidence,
            )
            return answer, GROQ_ANSWER_MODEL

        except Exception as groq_error:
            log.error(
                f"[GROQ ANSWER FAILED] model={GROQ_ANSWER_MODEL} error={groq_error}"
            )
            raise RuntimeError("Both Gemini and Groq answer failed")


# ---------------- MAIN AGENTIC FLOW ----------------
def agentic_qna(user_id: str, doc_id: str, question: str):
    start = time.time()

    question = normalize_text(question)
    if not question:
        return {"error": "Question is required"}

    qna_id = str(uuid.uuid4())
    rewrite_used = False

    # 1) document check
    doc = get_document(user_id=user_id, doc_id=doc_id)
    if not doc:
        return {"error": "Document not found"}

    if doc.get("status") != "ready":
        return {
            "http_status": 409,
            "status": doc.get("status"),
            "message": "Deep analysis is still running.",
        }

    # 2) initial retrieval
    matches = pinecone_query(user_id, doc_id, question, TOP_K_INITIAL)
    context, citations, best_score = build_context(matches)

    # 3) optional rewrite only if evidence is not strong
    elapsed_ms = int((time.time() - start) * 1000)
    if not has_strong_evidence(best_score, citations) and elapsed_ms <= MAX_REWRITE_BUDGET_MS:
        try:
            rewritten_query, rewrite_model_used = rewrite_query(question)
            if rewritten_query and rewritten_query.lower() != question.lower():
                rewrite_used = True
                log.info(f"[REWRITE SUCCESS] model={rewrite_model_used}")
                matches = pinecone_query(user_id, doc_id, rewritten_query, TOP_K_RETRY)
                context, citations, best_score = build_context(matches)
        except Exception as e:
            log.warning(
                f"[AGENTIC REWRITE FAILED] user_id={user_id} doc_id={doc_id} error={e}"
            )

    confidence = get_confidence_level(best_score, citations)

    log.info(
        f"[RETRIEVAL CHECK] best_score={best_score} "
        f"citations={len(citations)} confidence={confidence}"
    )

    # 4) return not_found only when there is no evidence at all
    if not has_any_evidence(citations):
        answer = "Not found in context."
        latency_ms = int((time.time() - start) * 1000)

        return _log_and_return(
            qna_id=qna_id,
            user_id=user_id,
            doc_id=doc_id,
            question=question,
            answer=answer,
            rewrite_used=rewrite_used,
            used_model="none",
            best_score=best_score,
            latency_ms=latency_ms,
            citations=citations,
            status="not_found",
            confidence="none",
        )

    # 5) answer whenever context exists
    complex_question = is_complex_question(question)

    try:
        answer, used_model = answer_with_selected_provider(
            question=question,
            context=context,
            complex_question=complex_question,
            confidence=confidence,
        )

        status = "answered" if confidence in {"high", "medium"} else "answered_low_confidence"

    except Exception as e:
        log.exception(
            f"[AGENTIC ANSWER FAILED] user_id={user_id} doc_id={doc_id} error={e}"
        )

        # Local extractive fallback instead of generic failure
        answer = extractive_fallback_answer(question, context)
        used_model = "local_extractive_fallback"
        status = "answered_fallback"

    latency_ms = int((time.time() - start) * 1000)

    return _log_and_return(
        qna_id=qna_id,
        user_id=user_id,
        doc_id=doc_id,
        question=question,
        answer=answer,
        rewrite_used=rewrite_used,
        used_model=used_model,
        best_score=best_score,
        latency_ms=latency_ms,
        citations=citations,
        status=status,
        confidence=confidence,
    )