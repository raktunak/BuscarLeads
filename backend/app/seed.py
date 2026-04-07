"""Seed database with verticals and regions from YAML files."""

import asyncio
import sys
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.region import Region
from app.models.vertical import Vertical

DATA_DIR = Path(__file__).parent.parent / "data"


async def seed_verticals(db: AsyncSession) -> int:
    data = yaml.safe_load((DATA_DIR / "verticals.yaml").read_text(encoding="utf-8"))
    count = 0

    for v in data.get("verticals", []):
        stmt = select(Vertical).where(Vertical.slug == v["slug"])
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.display_name = v["display_name"]
            existing.search_terms = v["search_terms"]
            existing.cnae_codes = v.get("cnae_codes", [])
            existing.estimated_no_web_pct = v.get("estimated_no_web_pct", "0")
            existing.icon = v.get("icon", "")
        else:
            db.add(Vertical(
                slug=v["slug"],
                display_name=v["display_name"],
                search_terms=v["search_terms"],
                cnae_codes=v.get("cnae_codes", []),
                estimated_no_web_pct=v.get("estimated_no_web_pct", "0"),
                icon=v.get("icon", ""),
            ))
            count += 1

    await db.commit()
    return count


async def seed_regions(db: AsyncSession) -> int:
    data = yaml.safe_load((DATA_DIR / "regions.yaml").read_text(encoding="utf-8"))
    count = 0

    for r in data.get("regions", []):
        stmt = select(Region).where(
            Region.name == r["name"],
            Region.country_code == r["country_code"],
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.center_lat = r.get("center_lat")
            existing.center_lng = r.get("center_lng")
            existing.timezone = r.get("timezone", "Europe/Madrid")
            existing.language = r.get("language", "es")
            existing.population = r.get("population", "")
        else:
            db.add(Region(
                name=r["name"],
                country_code=r["country_code"],
                region_type=r.get("region_type", "city"),
                center_lat=r.get("center_lat"),
                center_lng=r.get("center_lng"),
                timezone=r.get("timezone", "Europe/Madrid"),
                language=r.get("language", "es"),
                population=r.get("population", ""),
            ))
            count += 1

    await db.commit()
    return count


async def run_seed():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        v_count = await seed_verticals(db)
        r_count = await seed_regions(db)
        print(f"Seeded {v_count} new verticals, {r_count} new regions")


if __name__ == "__main__":
    asyncio.run(run_seed())
