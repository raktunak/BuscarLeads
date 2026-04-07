from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.business import Business
from app.models.campaign import Campaign
from app.models.user import User
from app.models.vertical import Vertical

router = APIRouter()


class DashboardStats(BaseModel):
    total_leads: int = 0
    leads_no_web: int = 0
    leads_with_phone: int = 0
    total_campaigns: int = 0
    campaigns_completed: int = 0
    avg_lead_score: float = 0.0
    leads_by_country: dict[str, int] = {}
    leads_by_status: dict[str, int] = {}


class VerticalStats(BaseModel):
    slug: str
    name: str
    total_leads: int
    leads_no_web: int
    avg_score: float


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Total leads
    total = (await db.execute(select(func.count(Business.id)))).scalar() or 0

    # Leads without website
    no_web = (await db.execute(
        select(func.count(Business.id)).where(Business.website_status.in_(["none", "dead", "parked"]))
    )).scalar() or 0

    # Leads with phone
    with_phone = (await db.execute(
        select(func.count(Business.id)).where(Business.phone_e164.isnot(None))
    )).scalar() or 0

    # Campaigns
    total_campaigns = (await db.execute(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    )).scalar() or 0

    completed_campaigns = (await db.execute(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id, Campaign.status == "completed")
    )).scalar() or 0

    # Average score
    avg_score = (await db.execute(select(func.avg(Business.lead_score)))).scalar() or 0.0

    # By country
    country_rows = (await db.execute(
        select(Business.country_code, func.count(Business.id)).group_by(Business.country_code)
    )).all()
    leads_by_country = {row[0]: row[1] for row in country_rows}

    # By website status
    status_rows = (await db.execute(
        select(Business.website_status, func.count(Business.id)).group_by(Business.website_status)
    )).all()
    leads_by_status = {(row[0] or "unknown"): row[1] for row in status_rows}

    return DashboardStats(
        total_leads=total,
        leads_no_web=no_web,
        leads_with_phone=with_phone,
        total_campaigns=total_campaigns,
        campaigns_completed=completed_campaigns,
        avg_lead_score=round(float(avg_score), 1),
        leads_by_country=leads_by_country,
        leads_by_status=leads_by_status,
    )


@router.get("/verticals", response_model=list[VerticalStats])
async def get_vertical_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Vertical.slug,
            Vertical.display_name,
            func.count(Business.id).label("total"),
            func.count(Business.id).filter(Business.website_status.in_(["none", "dead", "parked"])).label("no_web"),
            func.coalesce(func.avg(Business.lead_score), 0).label("avg_score"),
        )
        .outerjoin(Business, Business.vertical_id == Vertical.id)
        .group_by(Vertical.id)
        .order_by(func.count(Business.id).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        VerticalStats(
            slug=row[0],
            name=(row[1] or {}).get("es", row[0]),
            total_leads=row[2],
            leads_no_web=row[3],
            avg_score=round(float(row[4]), 1),
        )
        for row in rows
    ]
