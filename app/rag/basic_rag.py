# app/rag/qna.py
import os
import logging
from typing import Any
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("qna")

# Embeddings (same model as indexing)
ST_MODEL_NAME = os.getenv("ST_MODEL_NAME", "all-MiniLM-L6-v2")
embedder = SentenceTransformer(ST_MODEL_NAME)

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# LLM (Gemini)
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash"),
    temperature=0,
)

DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "9000"))


def _build_context(matches: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """
    Build context string + citations list.
    Pinecone metadata already includes text/page/filename/chunk_index. :contentReference[oaicite:10]{index=10}
    """
    blocks = []
    cites = []

    total_chars = 0
    for m in matches:
        md = (m.get("metadata") or {})
        text = (md.get("text") or "").strip()
        if not text:
            continue

        filename = md.get("filename")
        page = md.get("page")
        chunk_index = md.get("chunk_index")

        block = f"[source: {filename} | page: {page} | chunk: {chunk_index}]\n{text}"
        if total_chars + len(block) > MAX_CONTEXT_CHARS:
            break

        blocks.append(block)
        total_chars += len(block)

        cites.append({
            "filename": filename,
            "page": page,
            "chunk_index": chunk_index,
            "score": m.get("score"),
        })

    return "\n\n---\n\n".join(blocks), cites


def answer_question(user_id: str, doc_id: str, question: str, top_k: int = DEFAULT_TOP_K):
    question = (question or "").strip()
    if not question:
        return {"error": "Question is required"}

    # 1) Embed query
    qvec = embedder.encode([question], normalize_embeddings=True)[0].tolist()

    # 2) Query Pinecone (doc isolation)
    res = index.query(
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
        filter={"user_id": user_id, "doc_id": doc_id},
    )

    matches = res.get("matches", []) if isinstance(res, dict) else (res.matches or [])
    if not matches:
        return {
            "answer": "I couldn't find relevant text in the document for that question.",
            "citations": [],
        }

    # 3) Build context + citations
    context, citations = _build_context(matches)

    # 4) LLM answer with strict grounding
    prompt = f"""
You are a legal document assistant.

Answer the user question using ONLY the provided context.
If the answer is not in the context, say: "Not found in the document."

Give a clear answer in simple language.
If helpful, mention page numbers from the sources.

Instruction:
Give the response in Simple Language , Explain like you are explaining a childe

Question:
{question}

Context:
{context}
""".strip()

    answer = llm.invoke(prompt).content

    return {
        "answer": answer,
        "citations": citations,
        "top_k": top_k,
    }