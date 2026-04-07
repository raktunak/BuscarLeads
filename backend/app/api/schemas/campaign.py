"""Pydantic schemas for campaign endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    vertical_id: UUID
    region_id: UUID


class CampaignResponse(BaseModel):
    id: UUID
    vertical_id: UUID
    region_id: UUID
    vertical_name: str = ""
    region_name: str = ""
    status: str
    total_found: int
    total_qualified: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    error_message: str | None = None

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]
    total: int
