"""Pydantic schemas for lead/business endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LeadResponse(BaseModel):
    id: UUID
    name: str
    phone: str | None = None
    phone_e164: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    postal_code: str | None = None
    country_code: str
    website_url: str | None = None
    website_status: str | None = None
    website_ssl: bool | None = None
    website_mobile: bool | None = None
    website_cms: str | None = None
    google_rating: float | None = None
    google_reviews: int | None = None
    google_maps_url: str | None = None
    categories: str | None = None
    lead_score: int = 0
    lista_robinson: bool = False
    data_source: str
    facebook_url: str | None = None
    instagram_url: str | None = None
    created_at: datetime
    last_enriched_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    leads: list[LeadResponse]
    total: int
    page: int
    per_page: int


class LeadFilters(BaseModel):
    campaign_id: UUID | None = None
    vertical_id: UUID | None = None
    country_code: str | None = None
    city: str | None = None
    website_status: str | None = None  # none, dead, parked, basic, professional
    min_score: int | None = None
    max_score: int | None = None
    has_phone: bool | None = None
    exclude_robinson: bool = True
    search: str | None = None
    sort_by: str = "lead_score"
    sort_order: str = "desc"
