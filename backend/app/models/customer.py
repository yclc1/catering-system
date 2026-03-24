"""Customer, MealRegistration, CustomerSettlement models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Customer(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    contact_person = Column(String(64))
    phone = Column(String(20))
    address = Column(Text)
    billing_type = Column(String(16), nullable=False, default="per_head")
    breakfast_price = Column(Numeric(10, 2), default=0)
    lunch_price = Column(Numeric(10, 2), default=0)
    dinner_price = Column(Numeric(10, 2), default=0)
    supper_price = Column(Numeric(10, 2), default=0)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    notes = Column(Text)

    meals = relationship("MealRegistration", back_populates="customer", lazy="dynamic")
    settlements = relationship("CustomerSettlement", back_populates="customer", lazy="dynamic")


class MealRegistration(AuditMixin, Base):
    __tablename__ = "meal_registrations"
    __table_args__ = (
        UniqueConstraint("customer_id", "meal_date", name="uq_meal_customer_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    meal_date = Column(Date, nullable=False, index=True)
    breakfast_count = Column(Integer, nullable=False, default=0)
    breakfast_amount = Column(Numeric(12, 2), nullable=False, default=0)
    lunch_count = Column(Integer, nullable=False, default=0)
    lunch_amount = Column(Numeric(12, 2), nullable=False, default=0)
    dinner_count = Column(Integer, nullable=False, default=0)
    dinner_amount = Column(Numeric(12, 2), nullable=False, default=0)
    supper_count = Column(Integer, nullable=False, default=0)
    supper_amount = Column(Numeric(12, 2), nullable=False, default=0)
    daily_total = Column(Numeric(12, 2), nullable=False, default=0)
    notes = Column(Text)
    month_closed = Column(Boolean, nullable=False, default=False)

    customer = relationship("Customer", back_populates="meals", foreign_keys=[customer_id], lazy="selectin")


class CustomerSettlement(AuditMixin, Base):
    __tablename__ = "customer_settlements"
    __table_args__ = (
        UniqueConstraint("customer_id", "settlement_month", name="uq_settlement_customer_month"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    settlement_month = Column(String(7), nullable=False, index=True)
    total_breakfast_count = Column(Integer, nullable=False, default=0)
    total_lunch_count = Column(Integer, nullable=False, default=0)
    total_dinner_count = Column(Integer, nullable=False, default=0)
    total_supper_count = Column(Integer, nullable=False, default=0)
    total_amount = Column(Numeric(14, 2), nullable=False, default=0)
    adjustment_amount = Column(Numeric(14, 2), nullable=False, default=0)
    final_amount = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(16), nullable=False, default="draft")
    settled_at = Column(String(32))
    notes = Column(Text)

    customer = relationship("Customer", back_populates="settlements", foreign_keys=[customer_id], lazy="selectin")
