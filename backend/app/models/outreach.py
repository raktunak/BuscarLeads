import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from sqlalchemy.orm import relationship


class OutreachLog(Base):
    __tablename__ = "outreach_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # called, emailed, whatsapp, meeting, sold, rejected
    notes = Column(Text)
    outcome = Column(String(50))  # no_answer, interested, not_interested, callback, closed
    call_duration_s = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="outreach_logs")
    user = relationship("User", back_populates="outreach_logs")


class RobinsonEntry(Base):
    __tablename__ = "robinson_list"

    phone_e164 = Column(String(20), primary_key=True)
    checked_at = Column(DateTime, default=datetime.utcnow)


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # google_places, perplexity, google_maps_scraper
    endpoint = Column(String(255))
    requests_count = Column(Integer, default=1)
    cost_cents = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)
