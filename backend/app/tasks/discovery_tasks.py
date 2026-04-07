"""Celery tasks for the discovery pipeline."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.discovery.dedup import normalize_name, normalize_phone
from app.discovery.engine import DiscoveryEngine
from app.enrichment.phone_normalizer import normalize_phone_e164
from app.models.business import Business, CampaignBusiness
from app.models.campaign import Campaign
from app.models.region import Region
from app.models.vertical import Vertical
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_async_session() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.database_url, pool_size=5)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=3)
def run_discovery(self, campaign_id: str):
    """Execute the full discovery pipeline for a campaign."""
    asyncio.run(_run_discovery_async(campaign_id))


async def _run_discovery_async(campaign_id: str):
    session_factory = _get_async_session()

    async with session_factory() as db:
        # Load campaign with related data
        campaign = await db.get(Campaign, campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return

        vertical = await db.get(Vertical, campaign.vertical_id)
        region = await db.get(Region, campaign.region_id)

        if not vertical or not region:
            campaign.status = "failed"
            campaign.error_message = "Vertical or region not found"
            await db.commit()
            return

        # Update status
        campaign.status = "running"
        campaign.started_at = datetime.utcnow()
        await db.commit()

        try:
            # Get search query in the region's language
            lang = region.language or "es"
            search_terms = vertical.search_terms or {}
            terms = search_terms.get(lang, search_terms.get("es", []))
            query = terms[0] if terms else vertical.slug

            # Determine density based on population
            population = int(region.population or "0")
            if population > 1_000_000:
                density = "dense"
            elif population > 300_000:
                density = "medium"
            else:
                density = "rural"

            # Run discovery
            engine = DiscoveryEngine(db)
            raw_businesses = await engine.run_campaign(
                search_query=query,
                center_lat=float(region.center_lat),
                center_lng=float(region.center_lng),
                radius_km=25.0 if density == "dense" else 35.0 if density == "medium" else 50.0,
                density=density,
                country_code=region.country_code,
            )

            # Store results in database
            stored = 0
            for raw in raw_businesses:
                phone_e164 = normalize_phone_e164(raw.phone, raw.country_code) if raw.phone else None

                # Check for existing business by phone or google_place_id
                existing = None
                if raw.google_place_id:
                    stmt = select(Business).where(Business.google_place_id == raw.google_place_id)
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                if not existing and phone_e164:
                    stmt = select(Business).where(Business.phone_e164 == phone_e164)
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                if existing:
                    # Link existing business to campaign
                    link = CampaignBusiness(
                        campaign_id=campaign.id,
                        business_id=existing.id,
                        source=raw.data_source,
                    )
                    db.add(link)
                else:
                    # Create new business
                    biz = Business(
                        name=raw.name,
                        name_normalized=normalize_name(raw.name),
                        phone=raw.phone,
                        phone_e164=phone_e164,
                        address=raw.address,
                        city=raw.city,
                        province=raw.province,
                        postal_code=raw.postal_code,
                        country_code=raw.country_code,
                        latitude=raw.latitude,
                        longitude=raw.longitude,
                        vertical_id=vertical.id,
                        categories=raw.categories,
                        google_place_id=raw.google_place_id or None,
                        google_rating=raw.google_rating,
                        google_reviews=raw.google_reviews,
                        google_maps_url=raw.google_maps_url,
                        website_url=raw.website_url or None,
                        website_status="none" if not raw.website_url else "unknown",
                        data_source=raw.data_source,
                    )
                    db.add(biz)
                    await db.flush()

                    link = CampaignBusiness(
                        campaign_id=campaign.id,
                        business_id=biz.id,
                        source=raw.data_source,
                    )
                    db.add(link)
                    stored += 1

            # Update campaign totals
            campaign.total_found = len(raw_businesses)
            campaign.total_qualified = stored
            campaign.status = "completed"
            campaign.completed_at = datetime.utcnow()
            await db.commit()

            logger.info(f"Campaign {campaign_id} completed: {stored} new businesses stored")

            # Trigger enrichment for new businesses
            from app.tasks.enrichment_tasks import enrich_campaign

            enrich_campaign.delay(campaign_id)

        except Exception as e:
            logger.error(f"Campaign {campaign_id} failed: {e}")
            campaign.status = "failed"
            campaign.error_message = str(e)[:500]
            await db.commit()
