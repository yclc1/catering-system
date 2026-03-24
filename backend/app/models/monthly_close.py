"""Monthly Close model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.database import Base
from app.models.base import AuditMixin


class MonthlyClose(AuditMixin, Base):
    __tablename__ = "monthly_closes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    close_month = Column(String(7), unique=True, nullable=False)
    status = Column(String(16), nullable=False, default="open")
    closed_by = Column(Integer, ForeignKey("users.id"))
    closed_at = Column(DateTime(timezone=True))
    reopened_by = Column(Integer, ForeignKey("users.id"))
    reopened_at = Column(DateTime(timezone=True))
    notes = Column(Text)
