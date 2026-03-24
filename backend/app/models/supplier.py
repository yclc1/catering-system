"""Supplier model."""
from sqlalchemy import Column, Integer, String, Text

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Supplier(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    contact_person = Column(String(64))
    phone = Column(String(20))
    address = Column(Text)
    bank_name = Column(String(128))
    bank_account = Column(String(64))
    tax_id = Column(String(64))
    notes = Column(Text)
