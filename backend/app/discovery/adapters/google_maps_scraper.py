"""Google Maps scraper using Playwright (Capa 1 - free, massive coverage).

Automates a headless Chromium browser to search Google Maps and extract
business listings. Rate-limited to avoid detection.
"""

import asyncio
import logging
import re

from playwright.async_api import Page, async_playwright

from app.config import settings
from app.discovery.adapters.base import DataSourceAdapter, RawBusiness

logger = logging.getLogger(__name__)

GOOGLE_MAPS_URL = "https://www.google.com/maps/search/{query}/@{lat},{lng},{zoom}z"
MAX_SCROLL_ATTEMPTS = 20
SCROLL_PAUSE_MS = 1500


class GoogleMapsScraper(DataSourceAdapter):
    """Scrapes Google Maps search results using a headless browser."""

    @property
    def source_name(self) -> str:
        return "google_maps_scraper"

    async def search(self, query: str, latitude: float, longitude: float, radius_km: float) -> list[RawBusiness]:
        """Search Google Maps for businesses and extract listing data.

        Opens Google Maps with the query centered on the given coordinates,
        scrolls through results, and extracts business data from each listing.
        """
        zoom = self._radius_to_zoom(radius_km)
        url = GOOGLE_MAPS_URL.format(query=query, lat=latitude, lng=longitude, zoom=zoom)

        businesses = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                locale="es-ES",
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )

            if settings.proxy_url:
                # Proxy is configured at browser level in production
                pass

            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Accept cookies if dialog appears
                try:
                    accept_btn = page.locator("button", has_text=re.compile(r"Aceptar|Accept", re.IGNORECASE))
                    await accept_btn.click(timeout=3000)
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass

                # Wait for results panel to load
                await page.wait_for_selector('[role="feed"]', timeout=15000)

                # Scroll through results to load all listings
                listing_urls = await self._scroll_and_collect(page)
                logger.info(f"Found {len(listing_urls)} listings for '{query}' near ({latitude}, {longitude})")

                # Extract data from each listing
                for i, listing_url in enumerate(listing_urls):
                    try:
                        biz = await self._extract_listing(page, listing_url)
                        if biz:
                            biz.data_source = self.source_name
                            businesses.append(biz)
                    except Exception as e:
                        logger.warning(f"Failed to extract listing {i}: {e}")

                    # Rate limiting between listings
                    if i < len(listing_urls) - 1:
                        await asyncio.sleep(settings.scrape_delay_seconds / 5)

            except Exception as e:
                logger.error(f"Scraping failed for '{query}' near ({latitude}, {longitude}): {e}")
            finally:
                await browser.close()

        # Rate limiting between searches
        await asyncio.sleep(settings.scrape_delay_seconds)

        return businesses

    async def _scroll_and_collect(self, page: Page) -> list[str]:
        """Scroll through the results panel and collect all listing URLs."""
        feed = page.locator('[role="feed"]')
        collected_urls: set[str] = set()
        last_count = 0
        stale_rounds = 0

        for _ in range(MAX_SCROLL_ATTEMPTS):
            # Get all listing links currently visible
            links = await feed.locator("a[href*='/maps/place/']").all()
            for link in links:
                href = await link.get_attribute("href")
                if href and "/maps/place/" in href:
                    collected_urls.add(href)

            if len(collected_urls) == last_count:
                stale_rounds += 1
                if stale_rounds >= 3:
                    break
            else:
                stale_rounds = 0
                last_count = len(collected_urls)

            # Scroll down in the results panel
            await feed.evaluate("el => el.scrollTop = el.scrollHeight")
            await page.wait_for_timeout(SCROLL_PAUSE_MS)

            # Check for "end of results" indicator
            end_marker = await page.locator("span", has_text=re.compile(r"final de|end of|No hay más", re.IGNORECASE)).count()
            if end_marker > 0:
                break

        return list(collected_urls)

    async def _extract_listing(self, page: Page, url: str) -> RawBusiness | None:
        """Navigate to a listing page and extract business data."""
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        try:
            name = await self._get_text(page, "h1")
            if not name:
                return None

            # Extract address, phone, website from info panel
            address = await self._extract_info_field(page, "address|dirección")
            phone = await self._extract_info_field(page, "phone|teléfono")
            website = await self._extract_website(page)
            rating, reviews = await self._extract_rating(page)
            categories = await self._extract_categories(page)

            # Extract coordinates from URL
            lat, lng = self._extract_coords_from_url(page.url)

            return RawBusiness(
                name=name,
                address=address,
                phone=phone,
                website_url=website,
                latitude=lat,
                longitude=lng,
                google_rating=rating,
                google_reviews=reviews,
                google_maps_url=url,
                categories=categories,
                data_source=self.source_name,
                raw_data={"url": url},
            )
        except Exception as e:
            logger.warning(f"Error extracting data from {url}: {e}")
            return None

    async def _get_text(self, page: Page, selector: str) -> str:
        """Get text content of first matching element."""
        try:
            el = page.locator(selector).first
            return (await el.text_content(timeout=3000) or "").strip()
        except Exception:
            return ""

    async def _extract_info_field(self, page: Page, field_pattern: str) -> str:
        """Extract a field from the business info panel using aria-label matching."""
        try:
            buttons = await page.locator(f"button[aria-label]").all()
            for btn in buttons:
                label = await btn.get_attribute("aria-label") or ""
                if re.search(field_pattern, label, re.IGNORECASE):
                    return label.split(":", 1)[-1].strip() if ":" in label else label
            return ""
        except Exception:
            return ""

    async def _extract_website(self, page: Page) -> str:
        """Extract website URL from the business listing."""
        try:
            links = await page.locator("a[data-item-id='authority']").all()
            if links:
                return await links[0].get_attribute("href") or ""
            # Fallback: look for website button
            links = await page.locator("a[aria-label*='sitio web'], a[aria-label*='website']").all()
            if links:
                return await links[0].get_attribute("href") or ""
            return ""
        except Exception:
            return ""

    async def _extract_rating(self, page: Page) -> tuple[float | None, int | None]:
        """Extract rating and review count."""
        try:
            rating_el = page.locator("div.F7nice span[aria-hidden='true']").first
            rating_text = await rating_el.text_content(timeout=2000)
            rating = float(rating_text.replace(",", ".")) if rating_text else None

            reviews_el = page.locator("div.F7nice span[aria-label]").first
            reviews_label = await reviews_el.get_attribute("aria-label") or ""
            reviews_match = re.search(r"(\d[\d.]*)", reviews_label.replace(".", "").replace(",", ""))
            reviews = int(reviews_match.group(1)) if reviews_match else None

            return rating, reviews
        except Exception:
            return None, None

    async def _extract_categories(self, page: Page) -> str:
        """Extract business categories."""
        try:
            cat_btn = page.locator("button[jsaction*='category']").first
            return (await cat_btn.text_content(timeout=2000) or "").strip()
        except Exception:
            return ""

    def _extract_coords_from_url(self, url: str) -> tuple[float | None, float | None]:
        """Extract latitude and longitude from Google Maps URL."""
        match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None

    def _radius_to_zoom(self, radius_km: float) -> int:
        """Convert search radius to appropriate Google Maps zoom level."""
        if radius_km <= 2:
            return 15
        elif radius_km <= 5:
            return 14
        elif radius_km <= 10:
            return 13
        elif radius_km <= 20:
            return 12
        elif radius_km <= 40:
            return 11
        elif radius_km <= 80:
            return 10
        else:
            return 9
