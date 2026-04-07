from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RawBusiness:
    """Raw business data from any data source, before dedup and enrichment."""

    name: str
    address: str = ""
    city: str = ""
    province: str = ""
    postal_code: str = ""
    country_code: str = ""
    phone: str = ""
    website_url: str = ""
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str = ""
    google_rating: float | None = None
    google_reviews: int | None = None
    google_maps_url: str = ""
    categories: str = ""
    data_source: str = ""
    raw_data: dict = field(default_factory=dict)


class DataSourceAdapter(ABC):
    """Abstract base class for all data source adapters."""

    @abstractmethod
    async def search(self, query: str, latitude: float, longitude: float, radius_km: float) -> list[RawBusiness]:
        """Search for businesses matching query near a location.

        Args:
            query: Search term (e.g. "clínicas dentales", "dentist")
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers

        Returns:
            List of raw business results
        """
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this data source."""
        ...
