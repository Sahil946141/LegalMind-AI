import os
import logging
from collections import Counter, defaultdict

from langchain_google_genai import ChatGoogleGenerativeAI

from app.db.connection import (
    get_doc_analysis,
    set_read_more_cache,
    set_page_wise_cache,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("explanation")

# LLM only for simple wording of read_more
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,
)


def _clean_text(value):
    return (value or "").strip()


def _is_failed_risk(value: str) -> bool:
    v = _clean_text(value).lower()
    return v.startswith("[analysis_failed]")


def _split_risks(risk_text: str) -> list[str]:
    """
    Risks are stored like:
    'Risk A | Risk B'
    """
    if not risk_text:
        return []

    parts = [p.strip() for p in risk_text.split("|")]
    return [p for p in parts if p]


def _extract_read_more_summary(clause_analysis: list[dict]) -> dict:
    """
    Deterministically extract the main points from clause_analysis_json.
    This is the factual base. LLM only rewrites this cleanly.
    """
    if not clause_analysis:
        return {
            "topics": [],
            "risks": [],
            "entities": [],
            "clause_count": 0,
            "page_count": 0,
            "filenames": [],
        }

    valid_rows = []
    for row in clause_analysis:
        classification = _clean_text(row.get("classification"))
        risks = _clean_text(row.get("risks"))
        entities = _clean_text(row.get("entities"))
        source_text = _clean_text(row.get("source_text"))

        if classification or risks or entities or source_text:
            valid_rows.append(row)

    if not valid_rows:
        return {
            "topics": [],
            "risks": [],
            "entities": [],
            "clause_count": 0,
            "page_count": 0,
            "filenames": [],
        }

    topic_counter = Counter()
    risk_counter = Counter()
    entity_counter = Counter()
    page_set = set()
    filename_set = set()

    for row in valid_rows:
        classification = _clean_text(row.get("classification"))
        risks = _clean_text(row.get("risks"))
        entities = _clean_text(row.get("entities"))
        page = row.get("page")
        filename = _clean_text(row.get("filename"))

        if classification and classification.lower() != "unknown":
            topic_counter[classification] += 1

        if risks and not _is_failed_risk(risks):
            for item in _split_risks(risks):
                risk_counter[item] += 1

        if entities:
            for item in [e.strip() for e in entities.split(",")]:
                if item:
                    entity_counter[item] += 1

        if page is not None:
            page_set.add(page)

        if filename:
            filename_set.add(filename)

    return {
        "topics": [name for name, _ in topic_counter.most_common(4)],
        "risks": [name for name, _ in risk_counter.most_common(4)],
        "entities": [name for name, _ in entity_counter.most_common(6)],
        "clause_count": len(valid_rows),
        "page_count": len(page_set),
        "filenames": sorted(filename_set)[:2],
    }


def _build_fallback_read_more(summary: dict) -> str:
    """
    Local fallback if LLM fails for any reason.
    """
    topics = summary.get("topics", [])
    risks = summary.get("risks", [])
    entities = summary.get("entities", [])
    clause_count = summary.get("clause_count", 0)
    page_count = summary.get("page_count", 0)

    part1 = "This document appears to cover "
    part1 += ", ".join(topics) + "." if topics else "multiple contractual terms and obligations."

    part2 = f"It contains {clause_count} analyzed clauses"
    if page_count:
        part2 += f" across {page_count} page(s)"
    part2 += "."

    part3 = "The main risks identified are "
    part3 += ", ".join(risks) + "." if risks else "not clearly captured in the current analysis."

    if entities:
        part3 += f" Important entities mentioned include {', '.join(entities[:5])}."

    return f"{part1} {part2}\n\n{part3}"


def _frame_read_more_with_llm(summary: dict) -> str:
    """
    Use LLM only to write a simple, readable explanation.
    Do not let it invent facts beyond the structured summary.
    """
    prompt = f"""
You are given structured document-analysis data.

Write a simple, short explanation of what the document is about.
Use only the provided facts.
Do not add assumptions.
Keep it clear and natural.
Use 1-2 short paragraphs.
Do not use bullet points.

Structured summary:
- Topics: {summary.get("topics", [])}
- Risks: {summary.get("risks", [])}
- Entities: {summary.get("entities", [])}
- Clause count: {summary.get("clause_count", 0)}
- Page count: {summary.get("page_count", 0)}
- Filenames: {summary.get("filenames", [])}
""".strip()

    response = llm.invoke(prompt)
    return response.content.strip()


def read_more(user_id: str, doc_id: str):
    log.info(f"[READ_MORE] user_id={user_id} doc_id={doc_id}")

    row = get_doc_analysis(doc_id=doc_id, user_id=user_id)
    if not row or not row.get("clause_analysis_json"):
        return {"error": "No analysis found. Upload/process first."}

    # 1) Cache hit
    if row.get("read_more_cache"):
        log.info("[READ_MORE] cache hit")
        return {
            "explanation": row["read_more_cache"],
            "cached": True,
        }

    # 2) Build deterministic summary
    clause_analysis = row["clause_analysis_json"]
    summary = _extract_read_more_summary(clause_analysis)

    # 3) Use LLM only for wording, fallback locally if it fails
    try:
        explanation = _frame_read_more_with_llm(summary)
        if not explanation:
            explanation = _build_fallback_read_more(summary)
    except Exception as e:
        log.warning(f"[READ_MORE] llm framing failed, using fallback. error={e}")
        explanation = _build_fallback_read_more(summary)

    # 4) Save cache
    set_read_more_cache(
        doc_id=doc_id,
        user_id=user_id,
        text=explanation,
    )
    log.info("[READ_MORE] cache saved")

    return {
        "explanation": explanation,
        "cached": False,
    }


def page_wise(user_id: str, doc_id: str):
    """
    Deterministic summary per page (0 LLM calls).
    Great for quick risk scanning.
    """
    log.info(f"[PAGE_WISE] user_id={user_id} doc_id={doc_id}")

    row = get_doc_analysis(doc_id=doc_id, user_id=user_id)
    if not row or not row.get("clause_analysis_json"):
        return {"error": "No analysis found. Upload/process first."}

    # 1) Cache hit
    if row.get("page_wise_cache"):
        log.info("[PAGE_WISE] cache hit")
        return {
            "pages": row["page_wise_cache"],
            "cached": True,
        }

    clause_analysis = row["clause_analysis_json"]

    grouped = defaultdict(list)
    for clause in clause_analysis:
        key = (clause.get("filename"), clause.get("page"))
        grouped[key].append(clause)

    pages = []
    for (filename, page), clauses in grouped.items():
        classifications = list({
            c.get("classification", "")
            for c in clauses
            if c.get("classification")
        })
        risks = list({
            c.get("risks", "")
            for c in clauses
            if c.get("risks")
        })

        pages.append({
            "location": f"Page {page} – {filename}",
            "main_topics": classifications[:5],
            "key_risks": risks[:5],
            "clause_count": len(clauses),
        })

    pages.sort(key=lambda x: x["location"])

    # 2) Save cache
    set_page_wise_cache(
        doc_id=doc_id,
        user_id=user_id,
        page_json=pages,
    )

    log.info(f"[PAGE_WISE] cache saved pages={len(pages)}")

    return {
        "pages": pages,
        "cached": False,
    }