import os
import json
import time
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("clause_analyzis")


# ---------------- CONFIG ----------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "mistral")

TARGET_BATCH_SIZE = int(os.getenv("CLAUSE_BATCH_SIZE", "5"))
MAX_BATCH_SIZE = 5
TIMEOUT_SEC = int(os.getenv("OLLAMA_TIMEOUT_SEC", "720"))

MAX_RETRIES_PER_BATCH = int(os.getenv("CLAUSE_MAX_RETRIES", "1"))


# ---------------- MODEL CALL ----------------
def call_local_model(prompt: str) -> str:
    start = time.time()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LOCAL_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0,
            "format": "json",
        },
        timeout=TIMEOUT_SEC,
    )
    response.raise_for_status()

    payload = response.json()
    out = payload.get("response", "")

    log.info(
        f"[OLLAMA] model={LOCAL_MODEL} chars_in={len(prompt)} "
        f"chars_out={len(out)} time={round(time.time() - start,2)}s"
    )

    if not out.strip():
        raise ValueError("Empty response from model")

    return out


# ---------------- PROMPT ----------------
def build_batch_prompt(batch_items):

    expected_n = len(batch_items)
    expected_ids = ", ".join(f'"{cid}"' for cid, _ in batch_items)

    formatted = "\n\n---\n\n".join(
        f"Clause ID: {cid}\nTEXT:\n{text}"
        for cid, text in batch_items
    )

    return f"""
Return STRICT JSON only.

You will receive {expected_n} clauses with IDs:
[{expected_ids}]

You MUST return EXACTLY {expected_n} items.
Each Clause ID must appear exactly once.

Output format:

{{
  "items": [
    {{
      "chunk_id": "string",
      "classification": "string",
      "risks": "string",
      "entities": "string"
    }}
  ]
}}

CLASSIFICATION (choose one):
- Parties & Definitions
- Payment & Fees
- Term & Termination
- Confidentiality
- Intellectual Property
- Liability & Indemnity
- Warranties
- Data Protection
- Dispute Resolution
- Governing Law
- Service Levels
- Compliance
- Assignment
- Non-Compete / Non-Solicit
- Miscellaneous
- Unknown

RISKS:
Max 2 risks separated by " | ".

ENTITIES:
Extract companies, dates, money, jurisdictions, notice periods.

Clauses:
{formatted}
""".strip()


# ---------------- PARSING ----------------
def parse_items(raw):

    parsed = json.loads(raw)

    if "items" not in parsed:
        raise ValueError("JSON missing 'items'")

    items = parsed["items"]

    if not isinstance(items, list):
        raise ValueError("'items' must be a list")

    return items


def get_chunk_id(chunk):
    cid = chunk.metadata.get("chunk_index")
    if cid is None:
        raise ValueError("chunk_index missing")
    return str(cid)


# ---------------- VALIDATION ----------------
def validate_items(items, batch):

    expected_ids = [get_chunk_id(ch) for ch in batch]
    expected_set = set(expected_ids)

    valid_map = {}
    seen = set()

    for item in items:

        cid = str(item.get("chunk_id", "")).strip()

        if cid not in expected_set:
            continue

        if cid in seen:
            continue

        classification = item.get("classification")
        risks = item.get("risks")
        entities = item.get("entities")

        if classification is None or risks is None or entities is None:
            continue

        seen.add(cid)

        valid_map[cid] = {
            "classification": str(classification),
            "risks": str(risks),
            "entities": str(entities),
        }

    missing_ids = expected_set - set(valid_map.keys())

    return valid_map, missing_ids


# ---------------- RESULT BUILDERS ----------------
def build_rows(batch, valid_map):

    rows = []

    for chunk in batch:
        cid = get_chunk_id(chunk)
        item = valid_map[cid]

        rows.append({
            "classification": item["classification"],
            "risks": item["risks"],
            "entities": item["entities"],
            "source_text": chunk.page_content,
            "filename": chunk.metadata.get("filename"),
            "page": chunk.metadata.get("page"),
            "chunk_index": chunk.metadata.get("chunk_index"),
        })

    return rows


def fallback_rows(batch, error):

    rows = []

    for chunk in batch:
        rows.append({
            "classification": "",
            "risks": f"[analysis_failed] {error}",
            "entities": "",
            "source_text": chunk.page_content,
            "filename": chunk.metadata.get("filename"),
            "page": chunk.metadata.get("page"),
            "chunk_index": chunk.metadata.get("chunk_index"),
        })

    return rows


# ---------------- SINGLE RUN ----------------
def run_batch(batch, batch_id):

    chunk_ids = [get_chunk_id(ch) for ch in batch]

    log.info(f"[BATCH] {batch_id} size={len(batch)} ids={chunk_ids}")

    batch_items = [(get_chunk_id(ch), ch.page_content) for ch in batch]

    prompt = build_batch_prompt(batch_items)

    raw = call_local_model(prompt)

    items = parse_items(raw)

    valid_map, missing_ids = validate_items(items, batch)

    log.info(f"[VALID] batch={batch_id} valid={len(valid_map)} missing={missing_ids}")

    return valid_map, missing_ids


# ---------------- RECOVERY ----------------
def process_batch(batch, batch_id):

    last_error = None
    partial_valid = {}

    # retry full batch
    for attempt in range(MAX_RETRIES_PER_BATCH + 1):

        try:
            valid_map, missing_ids = run_batch(batch, batch_id)

            partial_valid = valid_map

            if not missing_ids:
                return build_rows(batch, partial_valid)

        except Exception as e:
            last_error = e
            log.warning(f"[WARN] batch={batch_id} attempt={attempt+1} error={e}")

    # retry only missing
    expected_ids = set(get_chunk_id(ch) for ch in batch)
    valid_ids = set(partial_valid.keys())

    missing = expected_ids - valid_ids

    if missing:

        retry_batch = [ch for ch in batch if get_chunk_id(ch) in missing]

        try:
            valid_map_retry, _ = run_batch(retry_batch, batch_id)

            partial_valid.update(valid_map_retry)

            if len(partial_valid) == len(batch):
                return build_rows(batch, partial_valid)

        except Exception as e:
            last_error = e

    # split if still failing
    if len(batch) > 1:

        mid = len(batch) // 2

        left = batch[:mid]
        right = batch[mid:]

        log.warning(f"[SPLIT] batch={batch_id} left={len(left)} right={len(right)}")

        rows = []

        rows.extend(process_batch(left, batch_id))
        rows.extend(process_batch(right, batch_id))

        return rows

    # fallback
    return fallback_rows(batch, str(last_error))


# ---------------- MAIN PIPELINE ----------------
def analyze_document_chunks(chunks):

    results = []

    total = len(chunks)

    batch_size = min(max(1, TARGET_BATCH_SIZE), MAX_BATCH_SIZE)

    log.info(f"[START] chunks={total} batch_size={batch_size}")

    i = 0
    batch_id = 0

    while i < total:

        batch_id += 1

        batch = chunks[i:i + batch_size]

        try:
            rows = process_batch(batch, batch_id)
            results.extend(rows)

        except Exception as e:
            log.exception(f"[FAIL] batch={batch_id}")
            results.extend(fallback_rows(batch, str(e)))

        i += len(batch)

    log.info(f"[DONE] processed={len(results)}")

    return results