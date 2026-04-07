"""Celery tasks for the enrichment and scoring pipeline."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.enrichment.pipeline import enrich_business
from app.models.business import Business, CampaignBusiness
from app.scoring.scorer import calculate_lead_score
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_async_session() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.database_url, pool_size=5)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=2)
def enrich_campaign(self, campaign_id: str):
    """Enrich and score all businesses from a campaign."""
    asyncio.run(_enrich_campaign_async(campaign_id))


async def _enrich_campaign_async(campaign_id: str):
    session_factory = _get_async_session()

    async with session_factory() as db:
        # Get all businesses linked to this campaign
        stmt = (
            select(Business)
            .join(CampaignBusiness)
            .where(CampaignBusiness.campaign_id == campaign_id)
            .where(Business.last_enriched_at.is_(None))
        )
        result = await db.execute(stmt)
        businesses = list(result.scalars().all())

        logger.info(f"Enriching {len(businesses)} businesses from campaign {campaign_id}")

        enriched = 0
        for biz in businesses:
            try:
                await enrich_business(biz, db)
                biz.lead_score = calculate_lead_score(biz)
                enriched += 1

                # Commit in batches of 20
                if enriched % 20 == 0:
                    await db.commit()
                    logger.info(f"  Enriched {enriched}/{len(businesses)}")

            except Exception as e:
                logger.warning(f"  Failed to enrich {biz.id}: {e}")

        await db.commit()
        logger.info(f"Enrichment complete: {enriched}/{len(businesses)} businesses")


@celery_app.task(bind=True)
def enrich_batch(self, business_ids: list[str]):
    """Enrich a specific batch of businesses by ID."""
    asyncio.run(_enrich_batch_async(business_ids))


async def _enrich_batch_async(business_ids: list[str]):
    session_factory = _get_async_session()

    async with session_factory() as db:
        stmt = select(Business).where(Business.id.in_(business_ids))
        result = await db.execute(stmt)
        businesses = list(result.scalars().all())

        for biz in businesses:
            try:
                await enrich_business(biz, db)
                biz.lead_score = calculate_lead_score(biz)
            except Exception as e:
                logger.warning(f"Failed to enrich {biz.id}: {e}")

        await db.commit()
