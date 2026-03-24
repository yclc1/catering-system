"""Account and payment schemas."""
from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class PaymentAccountCreate(BaseModel):
    name: str
    account_type: str  # bank, wechat, alipay, cash
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    current_balance: Decimal = Decimal("0")
    notes: Optional[str] = None


class PaymentAccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class PaymentAccountResponse(BaseModel):
    id: int
    code: str
    name: str
    account_type: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    current_balance: Decimal
    is_active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentRecordCreate(BaseModel):
    account_id: int
    direction: str  # inbound (收款) or outbound (付款)
    amount: Decimal
    payment_date: date
    counterparty_type: str  # customer or supplier
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    settlement_id: Optional[int] = None
    payment_method: Optional[str] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None


class PaymentRecordUpdate(BaseModel):
    amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None


class PaymentRecordResponse(BaseModel):
    id: int
    code: str
    account_id: int
    account_name: Optional[str] = None
    direction: str
    amount: Decimal
    payment_date: date
    counterparty_type: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    payment_method: Optional[str] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    month_closed: bool

    class Config:
        from_attributes = True
