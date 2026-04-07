from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.api.schemas.campaign import CampaignCreate, CampaignListResponse, CampaignResponse
from app.database import get_db
from app.models.campaign import Campaign
from app.models.region import Region
from app.models.user import User
from app.models.vertical import Vertical

router = APIRouter()


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = 1,
    per_page: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    # Count total
    count_stmt = select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch campaigns with related data
    stmt = (
        select(Campaign)
        .where(Campaign.user_id == user.id)
        .options(selectinload(Campaign.vertical), selectinload(Campaign.region))
        .order_by(Campaign.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    return CampaignListResponse(
        campaigns=[_to_response(c) for c in campaigns],
        total=total,
    )


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate vertical exists
    vertical = await db.get(Vertical, body.vertical_id)
    if not vertical:
        raise HTTPException(status_code=404, detail="Vertical not found")

    # Validate region exists
    region = await db.get(Region, body.region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    campaign = Campaign(
        user_id=user.id,
        vertical_id=body.vertical_id,
        region_id=body.region_id,
        status="pending",
    )
    db.add(campaign)
    await db.flush()

    # Trigger discovery task asynchronously
    from app.tasks.discovery_tasks import run_discovery

    run_discovery.delay(str(campaign.id))

    campaign.vertical = vertical
    campaign.region = region

    return _to_response(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == user.id)
        .options(selectinload(Campaign.vertical), selectinload(Campaign.region))
    )
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return _to_response(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)


def _to_response(campaign: Campaign) -> CampaignResponse:
    vertical_name = ""
    region_name = ""
    if campaign.vertical:
        names = campaign.vertical.display_name or {}
        vertical_name = names.get("es", names.get("en", ""))
    if campaign.region:
        region_name = campaign.region.name

    return CampaignResponse(
        id=campaign.id,
        vertical_id=campaign.vertical_id,
        region_id=campaign.region_id,
        vertical_name=vertical_name,
        region_name=region_name,
        status=campaign.status,
        total_found=campaign.total_found or 0,
        total_qualified=campaign.total_qualified or 0,
        started_at=campaign.started_at,
        completed_at=campaign.completed_at,
        created_at=campaign.created_at,
        error_message=campaign.error_message,
    )
