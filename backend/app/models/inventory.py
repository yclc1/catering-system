"""Inventory models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin


class InventoryTransaction(AuditMixin, Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    transaction_type = Column(String(16), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    reference_type = Column(String(32))
    reference_id = Column(Integer)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    status = Column(String(16), nullable=False, default="confirmed")
    total_amount = Column(Numeric(14, 2), nullable=False, default=0)
    notes = Column(Text)
    month_closed = Column(Boolean, nullable=False, default=False)

    supplier = relationship("Supplier", foreign_keys=[supplier_id], lazy="selectin")
    customer = relationship("Customer", foreign_keys=[customer_id], lazy="selectin")
    items = relationship("InventoryTransactionItem", back_populates="transaction", cascade="all, delete-orphan", lazy="selectin")


class InventoryTransactionItem(Base):
    __tablename__ = "inventory_transaction_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("inventory_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    batch_no = Column(String(32))

    transaction = relationship("InventoryTransaction", back_populates="items")
    product = relationship("Product", lazy="selectin")


class InventoryStock(Base):
    __tablename__ = "inventory_stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    current_qty = Column(Numeric(12, 3), nullable=False, default=0)
    avg_unit_cost = Column(Numeric(12, 4), nullable=False, default=0)
    last_inbound_date = Column(Date)
    last_outbound_date = Column(Date)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", lazy="selectin")
