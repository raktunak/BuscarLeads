import uuid

from sqlalchemy import Column, Numeric, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    country_code = Column(String(2), nullable=False, index=True)  # ISO 3166-1: ES, GB, MX, CO, CL, US, CA
    region_type = Column(String(50), nullable=False)  # city, province, state, country
    center_lat = Column(Numeric(10, 7))
    center_lng = Column(Numeric(10, 7))
    bounding_box = Column(JSON)  # {"ne_lat":..., "ne_lng":..., "sw_lat":..., "sw_lng":...}
    timezone = Column(String(50), default="Europe/Madrid")
    language = Column(String(10), default="es")
    population = Column(String(20), default="")

    campaigns = relationship("Campaign", back_populates="region")

    __table_args__ = (
        {"schema": None},
    )
