"""Audit Log model."""
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    username = Column(String(64), nullable=False)
    action = Column(String(16), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(Integer)
    resource_code = Column(String(32))
    detail = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
