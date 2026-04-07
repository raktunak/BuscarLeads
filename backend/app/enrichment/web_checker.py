"""Website presence and quality checker.

Checks if a business has a live website and assesses basic quality signals:
- HTTP status and SSL
- Mobile viewport meta tag
- CMS detection (WordPress, Wix, Squarespace, etc.)
- Page load time

Classifies websites into: none, dead, parked, basic, professional
"""

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10.0
MAX_REDIRECTS = 5


@dataclass
class WebCheckResult:
    status: str  # none, dead, parked, basic, professional
    ssl: bool = False
    mobile_friendly: bool = False
    cms: str = ""
    load_time_ms: int = 0
    final_url: str = ""
    status_code: int = 0


# Known parked/placeholder patterns
PARKED_PATTERNS = [
    r"domain.*(?:sale|parking|available|expired)",
    r"(?:esta|this).*(?:dominio|domain).*(?:venta|sale)",
    r"buy\s+this\s+domain",
    r"godaddy\.com/parking",
    r"sedoparking",
    r"hugedomains",
    r"dan\.com",
]

# CMS detection signatures
CMS_SIGNATURES = {
    "wordpress": [
        r'<meta name="generator" content="WordPress',
        r"/wp-content/",
        r"/wp-includes/",
    ],
    "wix": [
        r"wixsite\.com",
        r"<meta name=\"generator\" content=\"Wix",
        r"static\.wixstatic\.com",
    ],
    "squarespace": [
        r"squarespace\.com",
        r'<meta name="generator" content="Squarespace',
    ],
    "shopify": [
        r"cdn\.shopify\.com",
        r"myshopify\.com",
    ],
    "webflow": [
        r"webflow\.com",
        r"assets\.website-files\.com",
    ],
    "jimdo": [
        r"jimdo\.com",
        r"<meta name=\"generator\" content=\"Jimdo",
    ],
    "duda": [
        r"dudaone\.com",
        r"multiscreensite\.com",
    ],
}


async def check_website(url: str) -> WebCheckResult:
    """Check a website URL and return quality assessment.

    Args:
        url: The website URL to check

    Returns:
        WebCheckResult with status and quality signals
    """
    if not url or not url.strip():
        return WebCheckResult(status="none")

    # Ensure URL has protocol
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            timeout=REQUEST_TIMEOUT,
            verify=True,
        ) as client:
            import time

            start = time.monotonic()
            response = await client.get(url)
            load_time_ms = int((time.monotonic() - start) * 1000)

            result = WebCheckResult(
                status_code=response.status_code,
                ssl=str(response.url).startswith("https://"),
                final_url=str(response.url),
                load_time_ms=load_time_ms,
            )

            if response.status_code >= 400:
                result.status = "dead"
                return result

            html = response.text[:50000]  # Only analyze first 50KB

            # Check if parked domain
            if _is_parked(html):
                result.status = "parked"
                return result

            # Detect CMS
            result.cms = _detect_cms(html)

            # Check mobile friendliness
            result.mobile_friendly = _has_viewport(html)

            # Classify quality
            result.status = _classify_quality(result, html)

            return result

    except httpx.ConnectError:
        return WebCheckResult(status="dead")
    except httpx.TimeoutException:
        return WebCheckResult(status="dead")
    except Exception as e:
        logger.warning(f"Web check failed for {url}: {e}")
        return WebCheckResult(status="dead")


async def check_website_ssl_only(url: str) -> bool:
    """Quick check: does the website have valid SSL?"""
    if not url:
        return False
    if not url.startswith("https://"):
        url = f"https://{url.lstrip('http://')}"
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=True) as client:
            response = await client.head(url)
            return response.status_code < 400
    except Exception:
        return False


def _is_parked(html: str) -> bool:
    html_lower = html.lower()
    return any(re.search(pattern, html_lower) for pattern in PARKED_PATTERNS)


def _detect_cms(html: str) -> str:
    for cms_name, patterns in CMS_SIGNATURES.items():
        for pattern in patterns:
            if re.search(pattern, html, re.IGNORECASE):
                return cms_name
    return ""


def _has_viewport(html: str) -> bool:
    return bool(re.search(r'<meta[^>]*name=["\']viewport["\']', html, re.IGNORECASE))


def _classify_quality(result: WebCheckResult, html: str) -> str:
    """Classify website quality based on collected signals."""
    score = 0

    if result.ssl:
        score += 2
    if result.mobile_friendly:
        score += 2
    if result.cms:
        score += 1
    if result.load_time_ms < 3000:
        score += 1
    if len(html) > 5000:
        score += 1
    # Check for contact elements
    if re.search(r'tel:|whatsapp|wa\.me|formulario|contact|reserva', html, re.IGNORECASE):
        score += 2

    if score >= 6:
        return "professional"
    elif score >= 3:
        return "basic"
    else:
        return "basic"
