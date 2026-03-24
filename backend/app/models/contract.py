"""Contract and ContractReminder models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Contract(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=False)
    contract_type = Column(String(16), nullable=False)
    counterparty_type = Column(String(16))
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(14, 2))
    status = Column(String(16), nullable=False, default="active")
    file_url = Column(String(512))
    reminder_days_before = Column(Integer, nullable=False, default=30)
    notes = Column(Text)

    customer = relationship("Customer", foreign_keys=[customer_id], lazy="selectin")
    supplier = relationship("Supplier", foreign_keys=[supplier_id], lazy="selectin")
    reminders = relationship("ContractReminder", back_populates="contract", cascade="all, delete-orphan", lazy="selectin")


class ContractReminder(Base):
    __tablename__ = "contract_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_date = Column(Date, nullable=False)
    reminder_type = Column(String(16), nullable=False)
    message = Column(Text)
    is_sent = Column(Boolean, nullable=False, default=False)
    sent_at = Column(DateTime(timezone=True))
    recipient_user_id = Column(Integer, ForeignKey("users.id"))

    contract = relationship("Contract", back_populates="reminders")
    recipient = relationship("User", lazy="selectin")
