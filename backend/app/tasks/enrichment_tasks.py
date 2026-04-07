from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def enrich_batch(self, business_ids: list[str]):
    """Run enrichment pipeline on a batch of businesses."""
    # TODO: implement
    pass
