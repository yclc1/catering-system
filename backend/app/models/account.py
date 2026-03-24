"""Payment Account and Payment Record models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class PaymentAccount(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "payment_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    account_type = Column(String(16), nullable=False)
    bank_name = Column(String(128))
    account_number = Column(String(64))
    current_balance = Column(Numeric(14, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)


class PaymentRecord(AuditMixin, Base):
    __tablename__ = "payment_records"
    __table_args__ = (
        CheckConstraint(
            "(counterparty_type = 'customer' AND customer_id IS NOT NULL) OR "
            "(counterparty_type = 'supplier' AND supplier_id IS NOT NULL)",
            name="ck_payment_counterparty"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("payment_accounts.id"), nullable=False, index=True)
    direction = Column(String(8), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    payment_date = Column(Date, nullable=False, index=True)
    counterparty_type = Column(String(16), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True)
    settlement_id = Column(Integer)
    payment_method = Column(String(16))
    reference_no = Column(String(64))
    notes = Column(Text)
    month_closed = Column(Boolean, nullable=False, default=False)

    account = relationship("PaymentAccount", lazy="selectin")
    customer = relationship("Customer", foreign_keys=[customer_id], lazy="selectin")
    supplier = relationship("Supplier", foreign_keys=[supplier_id], lazy="selectin")
