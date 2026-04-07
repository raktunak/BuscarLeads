from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def run_discovery(self, campaign_id: str):
    """Execute discovery pipeline for a campaign: scrape -> dedup -> store."""
    # TODO: implement
    pass
