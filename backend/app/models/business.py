import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identity
    name = Column(String(500), nullable=False)
    name_normalized = Column(String(500), nullable=False, index=True)
    phone = Column(String(50))
    phone_e164 = Column(String(20), index=True)
    email = Column(String(255))

    # Location
    address = Column(Text)
    city = Column(String(255), index=True)
    province = Column(String(255))
    postal_code = Column(String(20))
    country_code = Column(String(2), nullable=False, index=True)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    location = Column(Geography("POINT", srid=4326))

    # Classification
    vertical_id = Column(UUID(as_uuid=True), ForeignKey("verticals.id"))
    categories = Column(Text)  # comma-separated Google categories

    # Google data
    google_place_id = Column(String(255), unique=True)
    google_rating = Column(Numeric(2, 1))
    google_reviews = Column(Integer)
    google_maps_url = Column(Text)

    # Web presence
    website_url = Column(Text)
    website_status = Column(String(20), default="unknown")  # none, dead, parked, basic, professional
    website_ssl = Column(Boolean)
    website_mobile = Column(Boolean)
    website_cms = Column(String(50))  # wordpress, wix, squarespace, etc.
    website_checked_at = Column(DateTime)

    # Social
    facebook_url = Column(Text)
    instagram_url = Column(Text)

    # Scoring
    lead_score = Column(Integer, default=0, index=True)  # 0-100

    # Compliance
    lista_robinson = Column(Boolean, default=False)

    # Metadata
    data_source = Column(String(50), nullable=False)  # google_maps_scraper, google_places_api, paginas_amarillas
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_enriched_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vertical = relationship("Vertical", back_populates="businesses")
    campaign_businesses = relationship("CampaignBusiness", back_populates="business")
    outreach_logs = relationship("OutreachLog", back_populates="business")


class CampaignBusiness(Base):
    __tablename__ = "campaign_businesses"

    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), primary_key=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), primary_key=True)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="campaign_businesses")
    business = relationship("Business", back_populates="campaign_businesses")
