"""Supplier Reconciliation model."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin


class SupplierReconciliation(AuditMixin, Base):
    __tablename__ = "supplier_reconciliations"
    __table_args__ = (
        UniqueConstraint("supplier_id", "reconciliation_month", name="uq_recon_supplier_month"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    reconciliation_month = Column(String(7), nullable=False, index=True)
    total_inbound_amount = Column(Numeric(14, 2), nullable=False, default=0)
    total_return_amount = Column(Numeric(14, 2), nullable=False, default=0)
    net_amount = Column(Numeric(14, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(14, 2), nullable=False, default=0)
    outstanding_amount = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(16), nullable=False, default="draft")
    notes = Column(Text)

    supplier = relationship("Supplier", foreign_keys=[supplier_id], lazy="selectin")
