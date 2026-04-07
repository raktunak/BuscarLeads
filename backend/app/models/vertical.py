import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Vertical(Base):
    __tablename__ = "verticals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(JSON, nullable=False)  # {"es": "Clínicas Dentales", "en": "Dental Clinics"}
    search_terms = Column(JSON, nullable=False)  # {"es": ["dentista", "clínica dental"], "en": ["dentist"]}
    cnae_codes = Column(ARRAY(Text), default=[])
    sic_codes = Column(ARRAY(Text), default=[])
    naics_codes = Column(ARRAY(Text), default=[])
    estimated_no_web_pct = Column(String(10), default="0")
    icon = Column(String(10), default="")

    campaigns = relationship("Campaign", back_populates="vertical")
    businesses = relationship("Business", back_populates="vertical")
