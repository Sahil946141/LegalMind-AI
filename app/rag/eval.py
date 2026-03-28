import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.db.connection import get_pg_connection
from app.core.security import hash_password

load_dotenv()

# -----------------------------
# 🔑 CONFIG
# -----------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "legal-doc-analyzer"

# Hardcoded evaluation user + document
EVAL_USER_ID = 999001
EVAL_USER_EMAIL = "evaluser@test.com"
EVAL_USER_PASSWORD = "EvalUser@123"

EVAL_DOC_ID = "a3f1c8b2-7e4d-4f5c-9b1e-123456789abc"
EVAL_DOC_NAME = "limeenergy_eval_document.json"
EVAL_DOC_FILE_PATH = "app/rag/pasted_content.json"

# -----------------------------
# 📥 LOAD JSON
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
json_path = BASE_DIR / "pasted_content.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# If your JSON is already plain text string
if isinstance(data, str):
    full_text = data
else:
    # if JSON is dict/list, convert safely into text
    full_text = json.dumps(data, ensure_ascii=False, indent=2)

print(f"Loaded text length: {len(full_text)}")

# -----------------------------
# ✂️ CHUNKING
# -----------------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=120
)

chunks = splitter.split_text(full_text)
print(f"Total chunks: {len(chunks)}")

# -----------------------------
# 🤖 LOAD EMBEDDING MODEL
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# 📡 PINECONE SETUP
# -----------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


# -----------------------------
# 🧑‍💻 CREATE / UPSERT FIXED USER IN POSTGRES
# -----------------------------
def ensure_eval_user():
    conn = get_pg_connection()
    try:
        cur = conn.cursor()

        password_hash = hash_password(EVAL_USER_PASSWORD)

        # Create fixed user if not exists
        # If email already exists, keep same user and activate it
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, is_active)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (email)
            DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                is_active = TRUE
            RETURNING id, email
            """,
            (EVAL_USER_ID, EVAL_USER_EMAIL, password_hash),
        )
        user = cur.fetchone()
        conn.commit()

        print(f"✅ Eval user ready: id={user['id']}, email={user['email']}")
        return str(user["id"])

    finally:
        conn.close()


# -----------------------------
# 📄 CREATE / UPSERT FIXED DOCUMENT IN POSTGRES
# -----------------------------
def ensure_eval_document(user_id: str):
    conn = get_pg_connection()
    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT doc_id
            FROM documents
            WHERE doc_id = %s AND user_id = %s
            """,
            (EVAL_DOC_ID, user_id),
        )
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """
                UPDATE documents
                SET doc_name = %s,
                    file_path = %s,
                    status = 'ready',
                    error_message = NULL,
                    updated_at = NOW()
                WHERE doc_id = %s AND user_id = %s
                """,
                (EVAL_DOC_NAME, EVAL_DOC_FILE_PATH, EVAL_DOC_ID, user_id),
            )
            print(f"✅ Eval document updated in DB: {EVAL_DOC_ID}")
        else:
            cur.execute(
                """
                INSERT INTO documents (doc_id, user_id, doc_name, file_path, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (EVAL_DOC_ID, user_id, EVAL_DOC_NAME, EVAL_DOC_FILE_PATH, "ready"),
            )
            print(f"✅ Eval document inserted in DB: {EVAL_DOC_ID}")

        conn.commit()

    finally:
        conn.close()


# -----------------------------
# 🧹 DELETE OLD PINECONE VECTORS FOR THIS DOC
# -----------------------------
def delete_existing_doc_vectors(document_id: str):
    try:
        # safest if your vector IDs are predictable
        ids_to_delete = [f"{document_id}_chunk_{i}" for i in range(len(chunks) + 500)]
        index.delete(ids=ids_to_delete)
        print("🧹 Old Pinecone vectors cleanup attempted")
    except Exception as e:
        print(f"⚠️ Could not delete old vectors: {e}")


# -----------------------------
# 🚀 UPSERT TO PINECONE
# -----------------------------
def upload_vectors(user_id: str):
    vectors = []

    for i, chunk in enumerate(chunks):
        vector_id = f"{EVAL_DOC_ID}_chunk_{i}"
        embedding = model.encode(chunk).tolist()

        vectors.append(
            {
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "document_id": EVAL_DOC_ID,
                    "doc_id": EVAL_DOC_ID,
                    "user_id": user_id,
                    "doc_name": EVAL_DOC_NAME,
                    "source": "sample_evaluation"
                },
            }
        )

    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)

    print("✅ Uploaded to Pinecone successfully!")


# -----------------------------
# ▶️ MAIN
# -----------------------------
if __name__ == "__main__":
    user_id = ensure_eval_user()
    ensure_eval_document(user_id=user_id)
    delete_existing_doc_vectors(EVAL_DOC_ID)
    upload_vectors(user_id=user_id)

    print("\n🎉 Setup complete")
    print(f"Login email    : {EVAL_USER_EMAIL}")
    print(f"Login password : {EVAL_USER_PASSWORD}")
    print(f"user_id        : {user_id}")
    print(f"document_id    : {EVAL_DOC_ID}")