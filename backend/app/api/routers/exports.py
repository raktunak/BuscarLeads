from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database import get_db
from app.export.csv_exporter import export_csv, export_excel
from app.models.business import Business, CampaignBusiness
from app.models.user import User

router = APIRouter()


@router.get("/csv")
async def export_leads_csv(
    campaign_id: UUID | None = None,
    min_score: int = 0,
    exclude_robinson: bool = True,
    website_status: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    businesses = await _get_export_businesses(db, campaign_id, min_score, exclude_robinson, website_status)
    csv_content = export_csv(businesses)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/excel")
async def export_leads_excel(
    campaign_id: UUID | None = None,
    min_score: int = 0,
    exclude_robinson: bool = True,
    website_status: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    businesses = await _get_export_businesses(db, campaign_id, min_score, exclude_robinson, website_status)
    excel_content = export_excel(businesses)

    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"},
    )


async def _get_export_businesses(
    db: AsyncSession,
    campaign_id: UUID | None,
    min_score: int,
    exclude_robinson: bool,
    website_status: str | None,
) -> list[Business]:
    stmt = select(Business).order_by(Business.lead_score.desc())

    if campaign_id:
        stmt = stmt.join(CampaignBusiness).where(CampaignBusiness.campaign_id == campaign_id)
    if min_score > 0:
        stmt = stmt.where(Business.lead_score >= min_score)
    if exclude_robinson:
        stmt = stmt.where(Business.lista_robinson == False)
    if website_status:
        stmt = stmt.where(Business.website_status == website_status)

    stmt = stmt.limit(10000)

    result = await db.execute(stmt)
    return list(result.scalars().all())
