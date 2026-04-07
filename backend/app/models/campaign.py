import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vertical_id = Column(UUID(as_uuid=True), ForeignKey("verticals.id"), nullable=False)
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed
    total_found = Column(Integer, default=0)
    total_qualified = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(String(500))

    user = relationship("User", back_populates="campaigns")
    vertical = relationship("Vertical", back_populates="campaigns")
    region = relationship("Region", back_populates="campaigns")
    campaign_businesses = relationship("CampaignBusiness", back_populates="campaign")
