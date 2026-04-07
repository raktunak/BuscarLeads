"""Discovery Engine - orchestrates data source queries, dedup, and storage.

This is the core module that coordinates the entire lead discovery pipeline:
1. Takes a vertical + region configuration
2. Generates search cells based on density strategy
3. Fans out queries to data source adapters
4. Deduplicates results
5. Stores raw businesses in the database
"""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.discovery.adapters.base import DataSourceAdapter, RawBusiness
from app.discovery.adapters.google_maps_scraper import GoogleMapsScraper
from app.discovery.dedup import deduplicate_businesses
from app.discovery.geo import generate_search_cells

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Orchestrates business discovery across data sources."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.adapters: list[DataSourceAdapter] = [
            GoogleMapsScraper(),
        ]

    async def run_campaign(
        self,
        search_query: str,
        center_lat: float,
        center_lng: float,
        radius_km: float,
        density: str,
        country_code: str = "ES",
    ) -> list[RawBusiness]:
        """Run a full discovery campaign for a vertical + region.

        Args:
            search_query: Localized search term (e.g. "clínicas dentales")
            center_lat: Region center latitude
            center_lng: Region center longitude
            radius_km: Region coverage radius
            density: Density level for grid strategy (dense/medium/rural)
            country_code: ISO country code for phone normalization

        Returns:
            Deduplicated list of raw businesses found
        """
        # Generate search cells based on density strategy
        cells = generate_search_cells(center_lat, center_lng, radius_km, density)
        logger.info(f"Generated {len(cells)} search cells for density={density}")

        all_results: list[RawBusiness] = []

        for adapter in self.adapters:
            logger.info(f"Running adapter: {adapter.source_name}")

            for i, cell in enumerate(cells):
                logger.info(
                    f"  Cell {i + 1}/{len(cells)}: "
                    f"({cell.latitude:.4f}, {cell.longitude:.4f}) r={cell.radius_km:.1f}km"
                )

                try:
                    results = await adapter.search(
                        query=search_query,
                        latitude=cell.latitude,
                        longitude=cell.longitude,
                        radius_km=cell.radius_km,
                    )

                    # Tag results with country code
                    for r in results:
                        if not r.country_code:
                            r.country_code = country_code

                    all_results.extend(results)
                    logger.info(f"    Found {len(results)} businesses")

                except Exception as e:
                    logger.error(f"    Adapter {adapter.source_name} failed on cell {i}: {e}")

        # Deduplicate across all results
        unique = deduplicate_businesses(all_results)
        logger.info(f"Total: {len(all_results)} raw -> {len(unique)} unique after dedup")

        return unique

    async def run_national_campaign(
        self,
        search_query: str,
        provinces: list[dict],
        country_code: str = "ES",
    ) -> list[RawBusiness]:
        """Run discovery across all provinces of a country.

        Args:
            search_query: Localized search term
            provinces: List of province configs with lat, lng, radius_km, density
            country_code: ISO country code

        Returns:
            Deduplicated list of all businesses found nationally
        """
        all_results: list[RawBusiness] = []

        for province in provinces:
            logger.info(f"=== Province: {province['name']} ({province['density']}) ===")

            results = await self.run_campaign(
                search_query=search_query,
                center_lat=province["lat"],
                center_lng=province["lng"],
                radius_km=province["radius_km"],
                density=province["density"],
                country_code=country_code,
            )
            all_results.extend(results)

        # Final dedup across provinces (border overlaps)
        unique = deduplicate_businesses(all_results)
        logger.info(f"National total: {len(all_results)} -> {len(unique)} unique")

        return unique
