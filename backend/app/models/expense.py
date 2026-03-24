"""Expense approval models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class ExpenseCategory(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "expense_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)


class ExpenseApproval(AuditMixin, Base):
    __tablename__ = "expense_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("expense_categories.id"), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    total_amount = Column(Numeric(14, 2), nullable=False)
    expense_date = Column(Date, nullable=False, index=True)
    status = Column(String(16), nullable=False, default="pending")
    approved_at = Column(DateTime(timezone=True))
    reject_reason = Column(Text)
    payment_account_id = Column(Integer, ForeignKey("payment_accounts.id"))
    payment_record_id = Column(Integer, ForeignKey("payment_records.id"))
    notes = Column(Text)
    photos = Column(JSON)
    month_closed = Column(Boolean, nullable=False, default=False)

    applicant = relationship("User", foreign_keys=[applicant_id], lazy="selectin")
    approver = relationship("User", foreign_keys=[approver_id], lazy="selectin")
    category = relationship("ExpenseCategory", lazy="selectin")
    items = relationship("ExpenseItem", back_populates="expense_approval", cascade="all, delete-orphan", lazy="selectin")


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_approval_id = Column(Integer, ForeignKey("expense_approvals.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(256), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    attachment_url = Column(String(512))

    expense_approval = relationship("ExpenseApproval", back_populates="items")
