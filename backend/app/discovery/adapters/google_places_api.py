"""Google Places API adapter (Capa 3 - validation of hot leads).

Uses the official Google Places API (New) for structured, reliable data.
Only used for high-score leads that passed Capa 1 scraping + Capa 2 enrichment.

Pricing:
- Basic fields (name, address, coords): FREE
- Contact fields (phone, website, hours): $3/1000 requests
- Atmosphere (rating, reviews): $5/1000 requests
- All fields: $32/1000 requests

Free tier: $200/month = ~66,000 Basic+Contact requests
"""

import logging

import httpx

from app.config import settings
from app.discovery.adapters.base import DataSourceAdapter, RawBusiness

logger = logging.getLogger(__name__)

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAIL_URL = "https://places.googleapis.com/v1/places/{place_id}"


class GooglePlacesApiAdapter(DataSourceAdapter):
    """Official Google Places API (New) adapter."""

    @property
    def source_name(self) -> str:
        return "google_places_api"

    async def search(self, query: str, latitude: float, longitude: float, radius_km: float) -> list[RawBusiness]:
        """Search using Google Places Text Search API.

        Uses field masks to control cost:
        - Basic (free): places.id, places.displayName, places.formattedAddress, places.location
        - Contact ($3/1000): places.nationalPhoneNumber, places.websiteUri
        - Atmosphere ($5/1000): places.rating, places.userRatingCount
        """
        if not settings.google_places_api_key:
            logger.warning("Google Places API key not configured")
            return []

        businesses = []
        next_page_token = None

        # Request up to 3 pages (60 results max)
        for page in range(3):
            try:
                results, next_page_token = await self._search_page(
                    query, latitude, longitude, radius_km, next_page_token
                )
                businesses.extend(results)

                if not next_page_token:
                    break

            except Exception as e:
                logger.error(f"Google Places API search failed (page {page}): {e}")
                break

        return businesses

    async def _search_page(
        self,
        query: str,
        latitude: float,
        longitude: float,
        radius_km: float,
        page_token: str | None = None,
    ) -> tuple[list[RawBusiness], str | None]:
        """Execute a single page of Text Search."""
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.google_places_api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.location,places.nationalPhoneNumber,places.websiteUri,"
                "places.rating,places.userRatingCount,places.googleMapsUri,"
                "places.types,places.primaryType,nextPageToken"
            ),
        }

        body = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius_km * 1000,  # API expects meters
                }
            },
            "languageCode": "es",
            "maxResultCount": 20,
        }

        if page_token:
            body["pageToken"] = page_token

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(PLACES_TEXT_SEARCH_URL, headers=headers, json=body)

            if response.status_code != 200:
                logger.error(f"Google Places API error {response.status_code}: {response.text}")
                return [], None

            data = response.json()

        businesses = []
        for place in data.get("places", []):
            location = place.get("location", {})
            biz = RawBusiness(
                name=place.get("displayName", {}).get("text", ""),
                address=place.get("formattedAddress", ""),
                phone=place.get("nationalPhoneNumber", ""),
                website_url=place.get("websiteUri", ""),
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                google_place_id=place.get("id", ""),
                google_rating=place.get("rating"),
                google_reviews=place.get("userRatingCount"),
                google_maps_url=place.get("googleMapsUri", ""),
                categories=place.get("primaryType", ""),
                data_source=self.source_name,
                raw_data=place,
            )
            businesses.append(biz)

        return businesses, data.get("nextPageToken")

    async def get_place_details(self, place_id: str) -> dict:
        """Get detailed information for a specific place.

        Used for validation of individual hot leads.
        """
        if not settings.google_places_api_key:
            return {}

        headers = {
            "X-Goog-Api-Key": settings.google_places_api_key,
            "X-Goog-FieldMask": (
                "id,displayName,formattedAddress,location,"
                "nationalPhoneNumber,internationalPhoneNumber,"
                "websiteUri,rating,userRatingCount,googleMapsUri,"
                "currentOpeningHours,priceLevel,types,primaryType"
            ),
        }

        url = PLACES_DETAIL_URL.format(place_id=place_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"Place details error {response.status_code}: {response.text}")
                return {}

            return response.json()
