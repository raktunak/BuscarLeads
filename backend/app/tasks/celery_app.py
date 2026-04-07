from celery import Celery

from app.config import settings

celery_app = Celery(
    "venderweb",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.discovery_tasks",
        "app.tasks.enrichment_tasks",
        "app.tasks.scoring_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
