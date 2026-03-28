import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extras import Json
from app.core.settings import settings


def get_pg_connection():
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )


# -------------------------
# Documents table functions
# -------------------------
def insert_document(doc_id: str, user_id: str, doc_name: str, file_path: str, status: str = "uploaded"):
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO documents (doc_id, user_id, doc_name, file_path, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (doc_id, user_id, doc_name, file_path, status),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def update_document_status(doc_id: str, user_id: str, status: str, error_message: str | None = None):
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE documents
            SET status=%s, error_message=%s, updated_at=NOW()
            WHERE doc_id=%s AND user_id=%s
            """,
            (status, error_message, doc_id, user_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def list_documents(user_id: str):
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT doc_id, doc_name, status, error_message, created_at, updated_at
        FROM documents
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "doc_id": row["doc_id"],
            "doc_name": row["doc_name"],
            "status": row["status"],
            "error_message": row["error_message"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]



def get_document(user_id: str, doc_id: str):
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT doc_id, user_id, doc_name, file_path, status, created_at, updated_at, error_message
        FROM documents
        WHERE user_id = %s AND doc_id = %s
        """,
        (user_id, doc_id),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "doc_id": row["doc_id"],
        "user_id": row["user_id"],
        "doc_name": row["doc_name"],
        "file_path": row["file_path"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "error_message": row["error_message"],
    }


def delete_document_db_records(user_id: str, doc_id: str):
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM qna_feedback WHERE user_id = %s AND doc_id = %s", (user_id, doc_id))
    except Exception:
        pass

    try:
        cur.execute("DELETE FROM qna_logs WHERE user_id = %s AND doc_id = %s", (user_id, doc_id))
    except Exception:
        pass

    try:
        cur.execute("DELETE FROM doc_analysis WHERE doc_id = %s", (doc_id,))
    except Exception:
        pass

    cur.execute(
        "DELETE FROM documents WHERE user_id = %s AND doc_id = %s",
        (user_id, doc_id),
    )

    conn.commit()
    cur.close()
    conn.close()


# -------------------------
# doc_analysis functions
# -------------------------
def upsert_doc_analysis(doc_id: str, clause_analysis_json):
    """
    Stores clause_analysis_json into doc_analysis as JSONB.
    """
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO doc_analysis (doc_id, clause_analysis_json, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (doc_id)
            DO UPDATE SET clause_analysis_json = EXCLUDED.clause_analysis_json,
                          updated_at = NOW()
            """,
            (doc_id, Json(clause_analysis_json)),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def get_doc_analysis(doc_id: str, user_id: str):
    """
    Returns clause_analysis_json + caches.
    Also ensures the doc belongs to this user.
    """
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT da.clause_analysis_json, da.read_more_cache, da.page_wise_cache
            FROM doc_analysis da
            JOIN documents d ON d.doc_id = da.doc_id
            WHERE da.doc_id=%s AND d.user_id=%s
            """,
            (doc_id, user_id),
        )
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        conn.close()


def set_read_more_cache(doc_id: str, user_id: str, text: str):
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE doc_analysis da
            SET read_more_cache=%s, updated_at=NOW()
            FROM documents d
            WHERE da.doc_id=d.doc_id AND da.doc_id=%s AND d.user_id=%s
            """,
            (text, doc_id, user_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def set_page_wise_cache(doc_id: str, user_id: str, page_json):
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE doc_analysis da
            SET page_wise_cache=%s::jsonb, updated_at=NOW()
            FROM documents d
            WHERE da.doc_id=d.doc_id AND da.doc_id=%s AND d.user_id=%s
            """,
            (Json(page_json), doc_id, user_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


# -------------------------
# Agentic QnA logs
# -------------------------
def insert_qna_log(
    qna_id: str,
    user_id: str,
    doc_id: str,
    question: str,
    answer: str,
    mode: str,
    rewrite_used: bool,
    used_model: str,
    best_score: float,
    latency_ms: int,
    citations_json,
    status: str,
):
    """
    Minimal agentic/basic QnA log storage.
    Expected table columns:
        qna_id TEXT PRIMARY KEY
        user_id TEXT NOT NULL
        doc_id TEXT NOT NULL
        question TEXT NOT NULL
        answer TEXT NOT NULL
        mode TEXT NOT NULL
        rewrite_used BOOLEAN DEFAULT FALSE
        used_model TEXT
        best_score DOUBLE PRECISION
        latency_ms INTEGER
        citations_json JSONB
        status TEXT
        created_at TIMESTAMP DEFAULT NOW()
    """
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO qna_logs (
                qna_id, user_id, doc_id, question, answer,
                mode, rewrite_used, used_model, best_score,
                latency_ms, citations_json, status, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, NOW())
            """,
            (
                qna_id,
                user_id,
                doc_id,
                question,
                answer,
                mode,
                rewrite_used,
                used_model,
                best_score,
                latency_ms,
                Json(citations_json),
                status,
            ),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def insert_qna_feedback(qna_id: str, user_id: str, doc_id: str, feedback: str):
    """
    Stores thumbs up/down or text feedback.
    Expected table columns:
        feedback_id SERIAL PRIMARY KEY (or UUID)
        qna_id TEXT
        user_id TEXT
        doc_id TEXT
        feedback TEXT
        created_at TIMESTAMP DEFAULT NOW()
    """
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO qna_feedback (qna_id, user_id, doc_id, feedback, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (qna_id, user_id, doc_id, feedback),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()
def clear_document_caches(doc_id: str, user_id: str):
    """
    Clears cached explanations when document analysis is regenerated.
    Verifies doc belongs to user via JOIN with documents table.
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE doc_analysis da
                SET read_more_cache = NULL,
                    page_wise_cache = NULL
                FROM documents d
                WHERE da.doc_id = d.doc_id 
                  AND da.doc_id = %s 
                  AND d.user_id = %s
                """,
                (doc_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()