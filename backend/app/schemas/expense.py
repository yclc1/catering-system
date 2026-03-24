"""Expense schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class ExpenseCategoryCreate(BaseModel):
    name: str
    sort_order: int = 0


class ExpenseCategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class ExpenseItemCreate(BaseModel):
    description: str
    amount: Decimal
    attachment_url: Optional[str] = None


class ExpenseApprovalCreate(BaseModel):
    approver_id: int
    category_id: int
    title: str
    total_amount: Decimal
    expense_date: date
    items: List[ExpenseItemCreate]
    notes: Optional[str] = None
    photos: Optional[List[str]] = None


class ExpenseApprovalUpdate(BaseModel):
    approver_id: Optional[int] = None
    category_id: Optional[int] = None
    title: Optional[str] = None
    total_amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    items: Optional[List[ExpenseItemCreate]] = None
    notes: Optional[str] = None
    photos: Optional[List[str]] = None


class ExpenseItemResponse(BaseModel):
    id: int
    description: str
    amount: Decimal
    attachment_url: Optional[str] = None

    class Config:
        from_attributes = True


class ExpenseApprovalResponse(BaseModel):
    id: int
    code: str
    applicant_id: int
    applicant_name: Optional[str] = None
    approver_id: int
    approver_name: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    title: str
    total_amount: Decimal
    expense_date: date
    status: str
    approved_at: Optional[str] = None
    reject_reason: Optional[str] = None
    items: List[ExpenseItemResponse] = []
    notes: Optional[str] = None
    photos: Optional[List[str]] = None
    month_closed: bool

    class Config:
        from_attributes = True


class RejectRequest(BaseModel):
    reason: str
