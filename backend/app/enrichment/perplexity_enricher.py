"""Perplexity API enrichment (Capa 2).

Uses the Perplexity API (already available to the team) to enrich leads with:
- Email addresses
- Social media profiles (Instagram, Facebook)
- Additional business context (years active, specialties)
- Website presence validation
"""

import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


async def enrich_with_perplexity(
    business_name: str,
    city: str,
    country_code: str = "ES",
    vertical: str = "",
) -> dict:
    """Query Perplexity API to find additional business data.

    Args:
        business_name: Name of the business
        city: City where the business is located
        country_code: ISO country code
        vertical: Business vertical for context

    Returns:
        Dict with enriched data: email, instagram, facebook, has_website, notes
    """
    if not settings.perplexity_api_key:
        logger.warning("Perplexity API key not configured, skipping enrichment")
        return {}

    country_name = {
        "ES": "España",
        "GB": "Reino Unido",
        "MX": "México",
        "CO": "Colombia",
        "CL": "Chile",
        "US": "Estados Unidos",
    }.get(country_code, country_code)

    prompt = (
        f"Busca información de contacto del negocio '{business_name}' "
        f"ubicado en {city}, {country_name}"
        f"{f', sector: {vertical}' if vertical else ''}. "
        f"Necesito: email de contacto, perfil de Instagram, perfil de Facebook, "
        f"y si tienen página web propia (no cuentan perfiles de redes sociales ni Google Maps). "
        f"Responde SOLO en formato JSON con las claves: "
        f"email, instagram, facebook, has_website (true/false), website_url, notes. "
        f"Si no encuentras un dato, usa null."
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PERPLEXITY_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.1,
                },
            )

            if response.status_code != 200:
                logger.error(f"Perplexity API error {response.status_code}: {response.text}")
                return {}

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Extract JSON from response
            return _parse_perplexity_response(content)

    except Exception as e:
        logger.error(f"Perplexity enrichment failed for '{business_name}': {e}")
        return {}


def _parse_perplexity_response(content: str) -> dict:
    """Parse the Perplexity API response and extract structured data."""
    # Try to find JSON in the response
    json_match = re.search(r"\{[^{}]+\}", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: extract individual fields
    result = {}
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", content)
    if email_match:
        result["email"] = email_match.group()

    ig_match = re.search(r"instagram\.com/([\w.]+)", content)
    if ig_match:
        result["instagram"] = f"https://instagram.com/{ig_match.group(1)}"

    fb_match = re.search(r"facebook\.com/([\w.]+)", content)
    if fb_match:
        result["facebook"] = f"https://facebook.com/{fb_match.group(1)}"

    return result
