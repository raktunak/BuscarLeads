from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.schemas.lead import LeadListResponse, LeadResponse
from app.database import get_db
from app.models.business import Business, CampaignBusiness
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    campaign_id: UUID | None = None,
    country_code: str | None = None,
    city: str | None = None,
    website_status: str | None = None,
    min_score: int | None = None,
    has_phone: bool | None = None,
    exclude_robinson: bool = True,
    search: str | None = None,
    sort_by: str = "lead_score",
    sort_order: str = "desc",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Business)
    count_stmt = select(func.count(Business.id))

    # Filter by campaign
    if campaign_id:
        stmt = stmt.join(CampaignBusiness).where(CampaignBusiness.campaign_id == campaign_id)
        count_stmt = count_stmt.join(CampaignBusiness).where(CampaignBusiness.campaign_id == campaign_id)

    # Filters
    if country_code:
        stmt = stmt.where(Business.country_code == country_code)
        count_stmt = count_stmt.where(Business.country_code == country_code)
    if city:
        stmt = stmt.where(Business.city.ilike(f"%{city}%"))
        count_stmt = count_stmt.where(Business.city.ilike(f"%{city}%"))
    if website_status:
        stmt = stmt.where(Business.website_status == website_status)
        count_stmt = count_stmt.where(Business.website_status == website_status)
    if min_score is not None:
        stmt = stmt.where(Business.lead_score >= min_score)
        count_stmt = count_stmt.where(Business.lead_score >= min_score)
    if has_phone is True:
        stmt = stmt.where(Business.phone_e164.isnot(None))
        count_stmt = count_stmt.where(Business.phone_e164.isnot(None))
    if exclude_robinson:
        stmt = stmt.where(Business.lista_robinson == False)
        count_stmt = count_stmt.where(Business.lista_robinson == False)
    if search:
        stmt = stmt.where(Business.name.ilike(f"%{search}%"))
        count_stmt = count_stmt.where(Business.name.ilike(f"%{search}%"))

    # Count
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = getattr(Business, sort_by, Business.lead_score)
    if sort_order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    # Paginate
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    leads = result.scalars().all()

    return LeadListResponse(
        leads=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await db.get(Business, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse.model_validate(business)
