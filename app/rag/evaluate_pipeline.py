import json
import time
from pathlib import Path
from typing import Any

import requests

# -----------------------------
# CONFIG
# -----------------------------
BASE_URL = "http://127.0.0.1:8000"

LOGIN_ENDPOINT = "/auth/login"
ASK_ENDPOINT = "/qna/agentic"

LOGIN_EMAIL = "evaluser@test.com"
LOGIN_PASSWORD = "EvalUser@123"

DOC_ID = "a3f1c8b2-7e4d-4f5c-9b1e-123456789abc"

QUESTIONS_FILE = Path(__file__).resolve().parent / "eval_questions.json"
OUTPUT_FILE = Path(__file__).resolve().parent / "evaluation_results_agentic.json"


# -----------------------------
# HELPERS
# -----------------------------
def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def load_questions() -> list[dict[str, Any]]:
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def login() -> str:
    url = f"{BASE_URL}{LOGIN_ENDPOINT}"

    data = {
        "username": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD,
    }

    response = requests.post(url, data=data, timeout=30)
    response.raise_for_status()

    result = response.json()
    token = result.get("access_token")

    if not token:
        raise ValueError("Login succeeded but no access_token found in response")

    return token


def ask_question(token: str, question: str) -> dict[str, Any]:
    url = f"{BASE_URL}{ASK_ENDPOINT}"

    headers = {
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "question": question,
        "doc_id": DOC_ID,
    }

    # IMPORTANT: use data= because endpoint expects Form(...)
    response = requests.post(url, data=payload, headers=headers, timeout=90)
    response.raise_for_status()
    return response.json()


def extract_answer(api_response: dict[str, Any]) -> str:
    return (
        api_response.get("answer")
        or api_response.get("response")
        or api_response.get("result")
        or ""
    )


def keyword_match_score(answer: str, expected_keywords: list[str]) -> tuple[bool, list[str]]:
    answer_norm = normalize_text(answer)

    matched = []
    for kw in expected_keywords:
        if normalize_text(kw) in answer_norm:
            matched.append(kw)

    passed = len(matched) == len(expected_keywords) if expected_keywords else False
    return passed, matched


def exact_or_keyword_match(
    answer: str,
    expected_answer: str | None,
    expected_keywords: list[str] | None
) -> tuple[str, bool, list[str]]:
    answer_norm = normalize_text(answer)
    matched_keywords: list[str] = []

    if expected_answer:
        if normalize_text(expected_answer) == answer_norm:
            return "exact_match", True, matched_keywords

    if expected_keywords:
        passed, matched_keywords = keyword_match_score(answer, expected_keywords)
        if passed:
            return "keyword_match", True, matched_keywords

    if expected_keywords:
        partial = []
        for kw in expected_keywords:
            if normalize_text(kw) in answer_norm:
                partial.append(kw)
        if partial:
            return "partial_keyword_match", False, partial

    return "no_match", False, matched_keywords


def evaluate_one(token: str, item: dict[str, Any], idx: int) -> dict[str, Any]:
    question = item["question"]
    expected_answer = item.get("expected_answer")
    expected_keywords = item.get("expected_keywords", [])
    category = item.get("category", "general")

    started = time.time()
    api_response = ask_question(token, question)
    latency_ms = int((time.time() - started) * 1000)

    actual_answer = extract_answer(api_response)

    match_type, passed, matched_keywords = exact_or_keyword_match(
        actual_answer,
        expected_answer,
        expected_keywords,
    )

    return {
        "question_number": idx,
        "category": category,
        "question": question,
        "expected_answer": expected_answer,
        "expected_keywords": expected_keywords,
        "actual_answer": actual_answer,
        "matched_keywords": matched_keywords,
        "match_type": match_type,
        "pass": passed,
        "latency_ms": latency_ms,
        "confidence": api_response.get("confidence"),
        "rewrite_used": api_response.get("rewrite_used"),
        "best_score": api_response.get("best_score"),
        "status": api_response.get("status"),
        "citations_count": len(api_response.get("citations", [])),
        "citations": api_response.get("citations", []),
        "raw_api_response": api_response,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    failed = total - passed

    by_category: dict[str, dict[str, int]] = {}
    by_confidence: dict[str, dict[str, int]] = {}
    rewrite_stats = {"used": 0, "not_used": 0}

    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, {"total": 0, "passed": 0, "failed": 0})
        by_category[cat]["total"] += 1
        if r["pass"]:
            by_category[cat]["passed"] += 1
        else:
            by_category[cat]["failed"] += 1

        conf = r.get("confidence") or "unknown"
        by_confidence.setdefault(conf, {"total": 0, "passed": 0, "failed": 0})
        by_confidence[conf]["total"] += 1
        if r["pass"]:
            by_confidence[conf]["passed"] += 1
        else:
            by_confidence[conf]["failed"] += 1

        if r.get("rewrite_used") is True:
            rewrite_stats["used"] += 1
        else:
            rewrite_stats["not_used"] += 1

    accuracy = (passed / total) if total else 0.0

    return {
        "total_questions": total,
        "passed": passed,
        "failed": failed,
        "accuracy": round(accuracy, 4),
        "by_category": by_category,
        "by_confidence": by_confidence,
        "rewrite_stats": rewrite_stats,
    }


def main():
    questions = load_questions()
    token = login()

    print("✅ Login successful")
    print(f"✅ Loaded {len(questions)} evaluation questions\n")

    results = []

    for idx, item in enumerate(questions, start=1):
        try:
            result = evaluate_one(token, item, idx)
            results.append(result)

            run_status = "PASS" if result["pass"] else "FAIL"
            print(f"[{run_status}] Q{idx}: {result['question']}")
            print(f"Answer: {result['actual_answer']}")
            print(f"Match Type: {result['match_type']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Rewrite Used: {result['rewrite_used']}")
            print(f"Best Score: {result['best_score']}")
            print(f"Status: {result['status']}")
            print(f"Citations Count: {result['citations_count']}")
            print(f"Latency: {result['latency_ms']} ms")
            print("-" * 100)

        except Exception as e:
            error_result = {
                "question_number": idx,
                "category": item.get("category", "general"),
                "question": item.get("question", ""),
                "expected_answer": item.get("expected_answer"),
                "expected_keywords": item.get("expected_keywords", []),
                "actual_answer": "",
                "matched_keywords": [],
                "match_type": "error",
                "pass": False,
                "latency_ms": None,
                "confidence": None,
                "rewrite_used": None,
                "best_score": None,
                "status": "error",
                "citations_count": 0,
                "citations": [],
                "error": str(e),
            }
            results.append(error_result)

            print(f"[ERROR] Q{idx}: {item.get('question', '')}")
            print(f"Error: {e}")
            print("-" * 100)

    summary = summarize_results(results)

    final_output = {
        "summary": summary,
        "results": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print("\n📊 FINAL SUMMARY")
    print(json.dumps(summary, indent=2))
    print(f"\n📁 Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()