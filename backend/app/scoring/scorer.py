"""Lead scoring module (0-100 points).

Assigns a priority score to each business based on how likely they are
to convert as a customer for our web services.

Higher score = better lead (more likely to need and pay for a website).

Scoring criteria:
- No website:               +40 pts (primary signal)
- No SSL / broken site:     +20 pts
- High Google rating:       +10 pts (successful business, can afford)
- Many reviews:              +5 pts (established business)
- Priority vertical:        +10 pts
- Not on Lista Robinson:    +10 pts (can actually be called)
- Has phone number:          +5 pts (reachable)
"""

from app.models.business import Business

# Verticals with highest conversion potential (slug -> bonus points)
PRIORITY_VERTICALS = {
    "dental_clinic": 10,
    "construction_renovation": 10,
    "lawyers": 10,
    "beauty_aesthetics": 8,
    "physiotherapy": 8,
    "restaurant": 5,
}


def calculate_lead_score(business: Business, vertical_slug: str = "") -> int:
    """Calculate lead score (0-100) for a business.

    Args:
        business: The business record to score
        vertical_slug: The vertical slug for priority bonus

    Returns:
        Integer score from 0 to 100
    """
    score = 0

    # Website presence (most important signal)
    if business.website_status == "none":
        score += 40
    elif business.website_status == "dead":
        score += 35
    elif business.website_status == "parked":
        score += 30
    elif business.website_status == "basic":
        if not business.website_ssl:
            score += 20
        elif not business.website_mobile:
            score += 15
        else:
            score += 5
    # professional = 0 points (they already have a good site)

    # Google reputation (indicates established business)
    if business.google_rating is not None:
        rating = float(business.google_rating)
        if rating >= 4.0:
            score += 10  # Successful business, can afford a site
        elif rating >= 3.0:
            score += 5

    if business.google_reviews is not None:
        if business.google_reviews >= 20:
            score += 5  # Established, not a new/failing business

    # Priority vertical bonus
    if vertical_slug in PRIORITY_VERTICALS:
        score += PRIORITY_VERTICALS[vertical_slug]

    # Compliance / reachability
    if not business.lista_robinson:
        score += 10
    if business.phone_e164:
        score += 5

    return min(score, 100)


def score_businesses(businesses: list[Business], vertical_slug: str = "") -> list[Business]:
    """Score a list of businesses and update their lead_score field.

    Returns the same list sorted by score descending.
    """
    for biz in businesses:
        biz.lead_score = calculate_lead_score(biz, vertical_slug)

    return sorted(businesses, key=lambda b: b.lead_score, reverse=True)
