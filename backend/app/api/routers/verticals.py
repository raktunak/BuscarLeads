from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.region import Region
from app.models.vertical import Vertical

router = APIRouter()


class VerticalResponse(BaseModel):
    id: str
    slug: str
    display_name: dict
    search_terms: dict
    estimated_no_web_pct: str
    icon: str

    model_config = {"from_attributes": True}


class RegionResponse(BaseModel):
    id: str
    name: str
    country_code: str
    region_type: str
    language: str
    population: str

    model_config = {"from_attributes": True}


@router.get("/verticals", response_model=list[VerticalResponse])
async def list_verticals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vertical).order_by(Vertical.slug))
    verticals = result.scalars().all()
    return [
        VerticalResponse(
            id=str(v.id), slug=v.slug, display_name=v.display_name or {},
            search_terms=v.search_terms or {}, estimated_no_web_pct=v.estimated_no_web_pct or "0",
            icon=v.icon or "",
        )
        for v in verticals
    ]


@router.get("/regions", response_model=list[RegionResponse])
async def list_regions(country_code: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Region).order_by(Region.country_code, Region.name)
    if country_code:
        stmt = stmt.where(Region.country_code == country_code)
    result = await db.execute(stmt)
    regions = result.scalars().all()
    return [
        RegionResponse(
            id=str(r.id), name=r.name, country_code=r.country_code,
            region_type=r.region_type, language=r.language or "es",
            population=r.population or "",
        )
        for r in regions
    ]
