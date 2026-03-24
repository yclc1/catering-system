"""PurchaseOrder and PurchaseOrderItem models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin


class PurchaseOrder(AuditMixin, Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    status = Column(String(16), nullable=False, default="draft")
    total_amount = Column(Numeric(14, 2), nullable=False, default=0)
    notes = Column(Text)
    month_closed = Column(Boolean, nullable=False, default=False)

    supplier = relationship("Supplier", foreign_keys=[supplier_id], lazy="selectin")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan", lazy="selectin")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    notes = Column(Text)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", lazy="selectin")
