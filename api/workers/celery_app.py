"""
Celery application configuration for background tasks.
"""

from celery import Celery
from config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "azmig_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

# Celery beat schedule for periodic tasks (if needed in future)
celery_app.conf.beat_schedule = {
    # Example: Clean up old validation jobs
    # 'cleanup-old-jobs': {
    #     'task': 'workers.tasks.cleanup_old_jobs',
    #     'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    # },
}

if __name__ == "__main__":
    celery_app.start()
