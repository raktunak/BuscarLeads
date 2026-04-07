"""Enrichment pipeline - runs all enrichment steps on discovered businesses.

Steps:
1. Normalize phone to E.164
2. Check website presence and quality
3. Cross-reference Lista Robinson (Spain)
4. Optional: Perplexity API enrichment (email, social, etc.)
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.phone_normalizer import normalize_phone_e164
from app.enrichment.web_checker import check_website
from app.models.business import Business
from app.models.outreach import RobinsonEntry

logger = logging.getLogger(__name__)


async def enrich_business(business: Business, db: AsyncSession) -> Business:
    """Run all enrichment steps on a single business record.

    Updates the business in-place with enriched data.
    """
    # 1. Phone normalization
    if business.phone and not business.phone_e164:
        business.phone_e164 = normalize_phone_e164(business.phone, business.country_code)

    # 2. Website check
    if business.website_url and business.website_status in ("unknown", None):
        result = await check_website(business.website_url)
        business.website_status = result.status
        business.website_ssl = result.ssl
        business.website_mobile = result.mobile_friendly
        business.website_cms = result.cms
        business.website_checked_at = datetime.utcnow()
    elif not business.website_url:
        business.website_status = "none"
        business.website_checked_at = datetime.utcnow()

    # 3. Lista Robinson check (Spain only)
    if business.country_code == "ES" and business.phone_e164:
        stmt = select(RobinsonEntry).where(RobinsonEntry.phone_e164 == business.phone_e164)
        result = await db.execute(stmt)
        robinson = result.scalar_one_or_none()
        business.lista_robinson = robinson is not None

    business.last_enriched_at = datetime.utcnow()
    return business


async def enrich_batch(business_ids: list[str], db: AsyncSession) -> int:
    """Enrich a batch of businesses by ID.

    Returns number of businesses successfully enriched.
    """
    enriched = 0
    stmt = select(Business).where(Business.id.in_(business_ids))
    result = await db.execute(stmt)
    businesses = result.scalars().all()

    for business in businesses:
        try:
            await enrich_business(business, db)
            enriched += 1
        except Exception as e:
            logger.error(f"Failed to enrich business {business.id}: {e}")

    await db.commit()
    logger.info(f"Enriched {enriched}/{len(businesses)} businesses")
    return enriched
