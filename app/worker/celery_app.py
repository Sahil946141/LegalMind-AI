import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "legal_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# On Windows, prefork/spawn semaphore handling can run into WinError 5 PermissionError.
# Prefer solo / threads pool to avoid named semaphore permission issues.
is_windows = os.name == "nt"
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
    task_track_started=os.getenv("CELERY_TASK_TRACK_STARTED", "true").lower() == "true",
    worker_prefetch_multiplier=int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")),
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "7200")),
    task_soft_time_limit=int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "6600")),
    broker_connection_retry_on_startup=True,
    task_default_queue="document_ingest",
    worker_pool=os.getenv("CELERY_WORKER_POOL", "solo" if is_windows else "prefork"),
    worker_concurrency=int(os.getenv("CELERY_WORKER_CONCURRENCY", "1" if is_windows else "4")),
)

celery_app.autodiscover_tasks(["app.worker"])