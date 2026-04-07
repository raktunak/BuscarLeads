"""Deduplication logic for business records.

Strategy (in priority order):
1. Exact match on normalized phone (E.164) -> same business
2. Same normalized name within 200m radius -> same business
3. Same Google Place ID -> same business

When merging duplicates, prefer the record with most complete data.
"""

import math
import re

from unidecode import unidecode

from app.discovery.adapters.base import RawBusiness
from app.discovery.geo import haversine

# Max distance in km to consider two businesses with same name as duplicates
DEDUP_RADIUS_KM = 0.2  # 200 meters


def normalize_name(name: str) -> str:
    """Normalize business name for comparison.

    Strips accents, lowercases, removes legal suffixes and punctuation.
    """
    name = unidecode(name).lower().strip()
    # Remove common legal suffixes
    suffixes = [
        r"\bs\.?l\.?\b", r"\bs\.?l\.?u\.?\b", r"\bs\.?a\.?\b",
        r"\bltd\.?\b", r"\bllc\b", r"\binc\.?\b", r"\bcorp\.?\b",
        r"\bs\.?c\.?p\.?\b", r"\bc\.?b\.?\b",
    ]
    for suffix in suffixes:
        name = re.sub(suffix, "", name)
    # Remove punctuation and extra whitespace
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_phone(phone: str) -> str:
    """Basic phone normalization: strip non-digits, add country prefix if missing."""
    if not phone:
        return ""
    digits = re.sub(r"[^\d+]", "", phone)
    if not digits:
        return ""
    return digits


def _completeness_score(biz: RawBusiness) -> int:
    """Score how complete a business record is (higher = more data)."""
    score = 0
    if biz.name:
        score += 1
    if biz.phone:
        score += 2
    if biz.address:
        score += 1
    if biz.website_url:
        score += 1
    if biz.google_rating is not None:
        score += 1
    if biz.google_reviews is not None:
        score += 1
    if biz.latitude is not None:
        score += 1
    if biz.google_place_id:
        score += 2
    return score


def deduplicate_businesses(businesses: list[RawBusiness]) -> list[RawBusiness]:
    """Remove duplicate businesses from a list.

    Uses phone number as primary dedup key, then falls back to
    name + geo proximity for businesses without phone.
    """
    if not businesses:
        return []

    # Index by normalized phone
    phone_index: dict[str, RawBusiness] = {}
    # Index by Google Place ID
    place_id_index: dict[str, RawBusiness] = {}
    # Businesses without phone for geo-based dedup
    no_phone: list[RawBusiness] = []

    for biz in businesses:
        # Check Google Place ID first
        if biz.google_place_id:
            if biz.google_place_id in place_id_index:
                existing = place_id_index[biz.google_place_id]
                if _completeness_score(biz) > _completeness_score(existing):
                    place_id_index[biz.google_place_id] = biz
                continue
            place_id_index[biz.google_place_id] = biz

        phone_norm = normalize_phone(biz.phone)
        if phone_norm and len(phone_norm) >= 9:
            # Use last 9 digits as key (handles country code variations)
            phone_key = phone_norm[-9:]
            if phone_key in phone_index:
                existing = phone_index[phone_key]
                if _completeness_score(biz) > _completeness_score(existing):
                    phone_index[phone_key] = biz
            else:
                phone_index[phone_key] = biz
        else:
            no_phone.append(biz)

    # Merge place_id results into phone results (phone takes precedence)
    for place_id, biz in place_id_index.items():
        phone_norm = normalize_phone(biz.phone)
        if phone_norm and len(phone_norm) >= 9:
            phone_key = phone_norm[-9:]
            if phone_key not in phone_index:
                phone_index[phone_key] = biz
        else:
            no_phone.append(biz)

    # Geo-based dedup for businesses without phone
    unique_no_phone: list[RawBusiness] = []
    for biz in no_phone:
        is_dup = False
        biz_name_norm = normalize_name(biz.name)

        if biz.latitude is not None and biz.longitude is not None:
            for existing in unique_no_phone:
                if existing.latitude is None or existing.longitude is None:
                    continue
                existing_name_norm = normalize_name(existing.name)
                if biz_name_norm == existing_name_norm:
                    dist = haversine(biz.latitude, biz.longitude, existing.latitude, existing.longitude)
                    if dist <= DEDUP_RADIUS_KM:
                        is_dup = True
                        break

        if not is_dup:
            unique_no_phone.append(biz)

    return list(phone_index.values()) + unique_no_phone
