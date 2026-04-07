import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="sales_rep")  # admin, manager, sales_rep
    language = Column(String(10), default="es")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="user")
    outreach_logs = relationship("OutreachLog", back_populates="user")
