"""Contract schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class ContractCreate(BaseModel):
    title: str
    contract_type: str  # customer, supplier, lease, service, other
    counterparty_type: Optional[str] = None  # customer or supplier
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    start_date: date
    end_date: date
    amount: Optional[Decimal] = None
    file_url: Optional[str] = None
    reminder_days_before: int = 30
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    contract_type: Optional[str] = None
    counterparty_type: Optional[str] = None
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None
    file_url: Optional[str] = None
    reminder_days_before: Optional[int] = None
    notes: Optional[str] = None


class ContractResponse(BaseModel):
    id: int
    code: str
    title: str
    contract_type: str
    counterparty_type: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    start_date: date
    end_date: date
    amount: Optional[Decimal] = None
    status: str
    file_url: Optional[str] = None
    reminder_days_before: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ContractReminderCreate(BaseModel):
    reminder_date: date
    reminder_type: str = "custom"
    message: Optional[str] = None
    recipient_user_id: Optional[int] = None


class ContractReminderResponse(BaseModel):
    id: int
    contract_id: int
    reminder_date: date
    reminder_type: str
    message: Optional[str] = None
    is_sent: bool
    recipient_user_id: Optional[int] = None

    class Config:
        from_attributes = True
