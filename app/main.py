from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pathlib import Path
import shutil
import uuid
import logging
import time
import os

from app.auth.router import router as auth_router
from app.auth.dependencies import get_current_user

from app.db.connection import (
    insert_document,
    update_document_status,
    list_documents,
    get_document,
    delete_document_db_records,
)

from app.rag.pipeline import delete_doc_vectors_from_pinecone
from app.rag.basic_rag import answer_question
from app.rag.explanation import read_more, page_wise
from app.rag.agentic_rag import agentic_qna
from app.worker.tasks import process_document_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("main")

app = FastAPI(
    title="Legal Analyzer Backend",
    # Increase the maximum request size for file uploads
    # This helps prevent issues with large files
)

# Add CORS middleware to allow frontend access
# In development, allow all origins for easier testing
if os.getenv("ENV", "dev") == "dev":
    log.info("Running in development mode - allowing all CORS origins")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    log.info("Running in production mode - using restricted CORS origins")
    # In production, be more restrictive
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8080", 
            # Add your production frontend URLs here
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

app.include_router(auth_router)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors, especially for file uploads with binary data
    """
    log.error(f"Validation error on {request.url}: {exc}")
    
    # Create a safe error response without trying to encode binary data
    error_details = []
    for error in exc.errors():
        safe_error = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error")
        }
        # Don't include the 'input' field which might contain binary data
        error_details.append(safe_error)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": error_details,
            "message": "Request validation failed. Please check your file and try again."
        }
    )

BASE_DATA_DIR = Path("data")
BASE_DATA_DIR.mkdir(exist_ok=True)


def _get_doc_or_404(user_id: str, doc_id: str):
    doc = get_document(user_id=user_id, doc_id=doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def _enforce_doc_status(
    user_id: str,
    doc_id: str,
    allowed_statuses: set[str],
    not_ready_message: str,
):
    doc = _get_doc_or_404(user_id=user_id, doc_id=doc_id)
    status = doc.get("status")

    if status in allowed_statuses:
        return doc

    if status == "failed":
        detail = {
            "status": status,
            "message": "Document processing failed.",
        }
        error_message = doc.get("error_message")
        if error_message:
            detail["error"] = error_message
        raise HTTPException(status_code=409, detail=detail)

    raise HTTPException(
        status_code=409,
        detail={
            "status": status,
            "message": not_ready_message,
        },
    )


@app.get("/health")
def health():
    # Test database connection
    try:
        from app.db.connection import get_pg_connection
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        db_status = "ok"
    except Exception as e:
        log.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"
    
    # Test Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    # Test Celery connection
    try:
        from app.worker.celery_app import celery_app
        # Try to get worker stats (this will fail if no workers are running)
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            celery_status = "ok"
        else:
            celery_status = "no_workers"
    except Exception as e:
        celery_status = f"error: {str(e)}"
    
    return {
        "status": "ok", 
        "message": "Legal Analyzer Backend is running",
        "services": {
            "database": db_status,
            "redis": redis_status,
            "celery": celery_status
        }
    }


@app.get("/test-cors")
def test_cors():
    """Simple endpoint to test CORS without authentication"""
    return {"status": "ok", "message": "CORS is working", "timestamp": time.time()}


@app.post("/init-db")
def init_database():
    """Initialize database tables - for development only"""
    try:
        from app.db.connection import get_pg_connection
        
        # Read and execute schema files
        schema_files = [
            "sql/auth_schema.sql",
            "sql/documents_schema.sql"
        ]
        
        conn = get_pg_connection()
        cur = conn.cursor()
        
        for schema_file in schema_files:
            if Path(schema_file).exists():
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                cur.execute(schema_sql)
                log.info(f"Executed schema: {schema_file}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "ok", "message": "Database initialized successfully"}
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")


@app.get("/test-auth")
def test_auth(current_user: dict = Depends(get_current_user)):
    """Test endpoint to verify authentication is working"""
    return {
        "status": "authenticated",
        "user_id": current_user["id"],
        "email": current_user["email"]
    }


@app.get("/documents")
def get_docs(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        log.info(f"[GET_DOCS] user_id={user_id}")
        docs = list_documents(user_id)
        log.info(f"[GET_DOCS] found {len(docs)} documents for user {user_id}")
        return {
            "user_id": user_id,
            "documents": docs,
        }
    except Exception as e:
        log.error(f"[GET_DOCS] error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@app.get("/documents/{doc_id}/status")
def doc_status(doc_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    doc = _get_doc_or_404(user_id=user_id, doc_id=doc_id)
    return {
        "doc_id": doc_id,
        "status": doc.get("status"),
        "error_message": doc.get("error_message"),
        "updated_at": doc.get("updated_at"),
    }


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload flow:
    - save file
    - insert document row as uploaded
    - enqueue Celery task
    - return immediately
    """
    t0 = time.time()
    
    log.info(f"[UPLOAD START] user_id={current_user['id']} filename={file.filename}")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Validate file type (common document types)
    allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )

    user_id = str(current_user["id"])
    doc_id = str(uuid.uuid4())

    doc_folder = BASE_DATA_DIR / user_id / doc_id
    doc_folder.mkdir(parents=True, exist_ok=True)

    save_path = doc_folder / file.filename
    
    try:
        # Read file content in chunks to handle large files better
        total_size = 0
        max_size = 50 * 1024 * 1024  # 50MB limit
        
        with save_path.open("wb") as buffer:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                total_size += len(chunk)
                if total_size > max_size:
                    # Clean up partial file
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")
                buffer.write(chunk)
        
        # Check if file is empty
        if total_size == 0:
            save_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="File is empty")
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        log.error(f"[UPLOAD FILE SAVE FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        # Clean up partial file
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to save file")

    log.info(f"[UPLOAD] user_id={user_id} doc_id={doc_id} saved_file={save_path}")

    log.info(f"[UPLOAD] user_id={user_id} doc_id={doc_id} saved_file={save_path}")

    try:
        insert_document(
            doc_id=doc_id,
            user_id=user_id,
            doc_name=file.filename,
            file_path=str(save_path),
            status="uploaded",
        )
    except Exception as e:
        log.error(f"[UPLOAD DB INSERT FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        # Clean up the saved file if DB insert fails
        try:
            save_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to save document record")

    try:
        # Try to enqueue the task with Celery
        task = process_document_task.delay(
            user_id=user_id,
            doc_id=doc_id,
            file_path=str(save_path),
        )

        log.info(
            f"[UPLOAD ENQUEUED] user_id={user_id} doc_id={doc_id} task_id={task.id} "
            f"time_sec={round(time.time() - t0, 2)}"
        )

        return {
            "message": "Upload received. Document queued for processing.",
            "user_id": user_id,
            "doc_id": doc_id,
            "doc_name": file.filename,
            "file_path": str(save_path),
            "status": "uploaded",
            "task_id": task.id,
            "qna_ready": False,
            "analysis_ready": False,
        }

    except Exception as e:
        # If Celery fails, update status and provide helpful error message
        error_msg = str(e)
        if "redis" in error_msg.lower() or "celery" in error_msg.lower():
            error_msg = "Document processing service is not available. Please ensure Redis and Celery worker are running."
        
        update_document_status(
            doc_id=doc_id,
            user_id=user_id,
            status="failed",
            error_message=error_msg,
        )
        log.exception(f"[UPLOAD ENQUEUE FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Task enqueue failed: {error_msg}")


@app.post("/qna")
def qna_api(
    doc_id: str = Form(...),
    question: str = Form(...),
    top_k: int = Form(5),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["id"])
    _enforce_doc_status(
        user_id=user_id,
        doc_id=doc_id,
        allowed_statuses={"indexed", "analyzing", "ready"},
        not_ready_message="Document is not ready for Q&A yet.",
    )
    return answer_question(user_id=user_id, doc_id=doc_id, question=question, top_k=top_k)


@app.post("/qna/agentic")
def qna_agentic_api(
    doc_id: str = Form(...),
    question: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["id"])
    _enforce_doc_status(
        user_id=user_id,
        doc_id=doc_id,
        allowed_statuses={"ready"},
        not_ready_message="Deep analysis is still running.",
    )
    return agentic_qna(user_id=user_id, doc_id=doc_id, question=question)


@app.post("/read_more")
def read_more_api(doc_id: str = Form(...), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    _enforce_doc_status(
        user_id=user_id,
        doc_id=doc_id,
        allowed_statuses={"ready"},
        not_ready_message="Deep analysis is still running.",
    )
    return read_more(user_id=user_id, doc_id=doc_id)


@app.post("/page_wise")
def page_wise_api(doc_id: str = Form(...), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    _enforce_doc_status(
        user_id=user_id,
        doc_id=doc_id,
        allowed_statuses={"ready"},
        not_ready_message="Deep analysis is still running.",
    )
    return page_wise(user_id=user_id, doc_id=doc_id)


@app.delete("/documents/{doc_id}")
def delete_doc(doc_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    doc = _get_doc_or_404(user_id=user_id, doc_id=doc_id)

    file_path = doc.get("file_path")
    if file_path:
        try:
            doc_folder = Path(file_path).parent
        except Exception:
            doc_folder = BASE_DATA_DIR / user_id / doc_id
    else:
        doc_folder = BASE_DATA_DIR / user_id / doc_id

    try:
        delete_doc_vectors_from_pinecone(user_id=user_id, doc_id=doc_id)
    except Exception as e:
        log.exception(f"[DELETE PINECONE FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete vectors: {e}")

    try:
        delete_document_db_records(user_id=user_id, doc_id=doc_id)
    except Exception as e:
        log.exception(f"[DELETE DB FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete DB records: {e}")

    try:
        if doc_folder.exists():
            shutil.rmtree(doc_folder, ignore_errors=True)
    except Exception as e:
        log.exception(f"[DELETE FILE FAILED] user_id={user_id} doc_id={doc_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")

    log.info(f"[DELETE DONE] user_id={user_id} doc_id={doc_id}")

    return {
        "status": "ok",
        "message": "Document deleted successfully.",
        "user_id": user_id,
        "doc_id": doc_id,
    }