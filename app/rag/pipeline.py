import os
import time
import logging
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from app.db.connection import clear_document_caches
from app.rag.ingest import load_document, chunk_documents
from app.rag.clause_analyzis import analyze_document_chunks
from app.db.connection import upsert_doc_analysis, update_document_status

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("pipeline")

# ----- Embeddings (local) -----
ST_MODEL_NAME = os.getenv("ST_MODEL_NAME", "all-MiniLM-L6-v2")
embedder = SentenceTransformer(ST_MODEL_NAME)

# ----- Pinecone -----
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

DIMENSION = int(os.getenv("PINECONE_DIMENSION", "384"))
CLOUD = os.getenv("PINECONE_CLOUD", "aws")
REGION = os.getenv("PINECONE_REGION", "us-east-1")

pc = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME not in pc.list_indexes().names():
    log.info(f"[PINECONE] Creating index name={INDEX_NAME} dim={DIMENSION} metric=cosine")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=CLOUD, region=REGION),
    )

index = pc.Index(INDEX_NAME)


def upsert_chunks_to_pinecone(user_id: str, doc_id: str, chunks):
    t0 = time.time()
    texts = [c.page_content for c in chunks]
    vectors_emb = embedder.encode(texts, normalize_embeddings=True).tolist()

    vectors = []
    for chunk, vec in zip(chunks, vectors_emb):
        filename = chunk.metadata.get("filename", "unknown")
        page = chunk.metadata.get("page")
        chunk_index = chunk.metadata.get("chunk_index")

        vector_id = f"{doc_id}:{chunk_index}"
        vectors.append(
            {
                "id": vector_id,
                "values": vec,
                "metadata": {
                    "user_id": user_id,
                    "doc_id": doc_id,
                    "filename": filename,
                    "page": page,
                    "chunk_index": chunk_index,
                    "text": chunk.page_content,
                },
            }
        )

    if vectors:
        index.upsert(vectors=vectors)

    log.info(
        f"[PINECONE UPSERT] user_id={user_id} doc_id={doc_id} "
        f"vectors={len(vectors)} time_sec={round(time.time() - t0, 2)}"
    )
    return len(vectors), len(chunks)


def process_document_in_background(user_id: str, doc_id: str, file_path: str):
    """
    Full active upload pipeline:
    uploaded -> indexed -> analyzing -> ready
    """
    overall_t0 = time.time()
    log.info(f"[BG PIPELINE START] user_id={user_id} doc_id={doc_id} file_path={file_path}")

    try:
        log.info(f"[BG STEP] user_id={user_id} doc_id={doc_id} loading document")
        docs = load_document(file_path)
        if not docs:
            raise ValueError("Unsupported file type or empty document")

        log.info(f"[BG STEP] user_id={user_id} doc_id={doc_id} loaded {len(docs)} pages")
        chunks = chunk_documents(docs)
        log.info(f"[BG STEP] user_id={user_id} doc_id={doc_id} split into {len(chunks)} chunks")

        log.info(f"[BG STEP] user_id={user_id} doc_id={doc_id} upserting chunks to Pinecone")
        stored_vectors, total_chunks = upsert_chunks_to_pinecone(
            user_id=user_id,
            doc_id=doc_id,
            chunks=chunks,
        )

        update_document_status(
            doc_id=doc_id,
            user_id=user_id,
            status="indexed",
        )
        log.info(f"[BG STEP] user_id={user_id} doc_id={doc_id} status -> indexed")

        update_document_status(
            doc_id=doc_id,
            user_id=user_id,
            status="analyzing",
        )
        log.info(f"[BG STEP] user_id={user_id} doc_id={doc_id} status -> analyzing")

        # ===============================
        # PHASE 2: CLEAR OLD CACHES
        # ===============================
        clear_document_caches(
            doc_id=doc_id,
            user_id=user_id
        )

        # Run clause analysis
        clause_analysis = analyze_document_chunks(chunks)

        # Store clause analysis
        upsert_doc_analysis(
            doc_id=doc_id,
            clause_analysis_json=clause_analysis,
        )

        update_document_status(
            doc_id=doc_id,
            user_id=user_id,
            status="ready",
        )

        log.info(
            f"[BG PIPELINE DONE] user_id={user_id} doc_id={doc_id} "
            f"stored_vectors={stored_vectors} total_chunks={total_chunks} "
            f"time_sec={round(time.time() - overall_t0, 2)}"
        )

    except Exception as e:
        log.exception(f"[BG PIPELINE FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        update_document_status(
            doc_id=doc_id,
            user_id=user_id,
            status="failed",
            error_message=str(e),
        )
        raise

def delete_doc_vectors_from_pinecone(user_id: str, doc_id: str):
    """
    Delete all vectors for one document using metadata filter.
    """
    index.delete(
        filter={
            "user_id": user_id,
            "doc_id": doc_id,
        }
    )

    log.info(f"[PINECONE DELETE] user_id={user_id} doc_id={doc_id}")