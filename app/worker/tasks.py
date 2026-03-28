import logging
from celery.exceptions import SoftTimeLimitExceeded

from app.worker.celery_app import celery_app
from app.rag.pipeline import process_document_in_background
from app.db.connection import update_document_status

log = logging.getLogger("worker.tasks")


@celery_app.task(
    bind=True,
    name="app.worker.tasks.process_document_task",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
    acks_late=True,
)
def process_document_task(self, user_id: str, doc_id: str, file_path: str):
    """
    Celery wrapper around the existing pipeline.
    Retries only for transient failures.
    """
    log.info(
        "[CELERY TASK START] task_id=%s user_id=%s doc_id=%s file_path=%s",
        self.request.id,
        user_id,
        doc_id,
        file_path,
    )

    try:
        process_document_in_background(
            user_id=user_id,
            doc_id=doc_id,
            file_path=file_path,
        )

        log.info(
            "[CELERY TASK DONE] task_id=%s user_id=%s doc_id=%s",
            self.request.id,
            user_id,
            doc_id,
        )

        return {
            "task_id": self.request.id,
            "user_id": user_id,
            "doc_id": doc_id,
            "status": "completed",
        }

    except SoftTimeLimitExceeded:
        log.exception(
            "[CELERY TASK TIMEOUT] task_id=%s user_id=%s doc_id=%s",
            self.request.id,
            user_id,
            doc_id,
        )
        update_document_status(
            doc_id=doc_id,
            user_id=user_id,
            status="failed",
            error_message="Document processing timed out.",
        )
        raise

    except Exception as e:
        log.exception(
            "[CELERY TASK FAIL] task_id=%s user_id=%s doc_id=%s error=%s",
            self.request.id,
            user_id,
            doc_id,
            e,
        )
        # process_document_in_background() already marks failed
        raise