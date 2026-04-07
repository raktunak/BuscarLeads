from app.tasks.celery_app import celery_app


@celery_app.task(bind=True)
def score_batch(self, business_ids: list[str]):
    """Recalculate lead scores for a batch of businesses."""
    # TODO: implement
    pass
