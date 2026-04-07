"""Common Pydantic schemas used across the API."""

from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class PaginatedParams(BaseModel):
    page: int = 1
    per_page: int = 50


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
