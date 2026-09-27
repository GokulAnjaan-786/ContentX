import os
import sys
from celery import Celery

# Ensure backend and project root are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings

import socket


def is_redis_available() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            s.connect(("localhost", 6379))
            return True
    except Exception:
        return False


redis_online = is_redis_available()

celery_app = Celery(
    "contentforge_worker",
    broker=settings.CELERY_BROKER_URL if redis_online else "memory://",
    backend=settings.CELERY_RESULT_BACKEND if redis_online else None,
    include=["worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,        # 5 minute timeout per task
    worker_prefetch_multiplier=1,
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_transport_options={"max_retries": 1},
    beat_schedule={
        "daily-data-retention-purge": {
            "task": "worker.tasks.enforce_data_retention_task",
            "schedule": 86400.0,  # Run daily every 24 hours
        },
    },
)

if __name__ == "__main__":
    celery_app.start()
