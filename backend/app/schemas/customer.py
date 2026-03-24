"""Customer schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class CustomerCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    billing_type: str = "per_head"
    breakfast_price: Decimal = Decimal("0")
    lunch_price: Decimal = Decimal("0")
    dinner_price: Decimal = Decimal("0")
    supper_price: Decimal = Decimal("0")
    contract_id: Optional[int] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    billing_type: Optional[str] = None
    breakfast_price: Optional[Decimal] = None
    lunch_price: Optional[Decimal] = None
    dinner_price: Optional[Decimal] = None
    supper_price: Optional[Decimal] = None
    contract_id: Optional[int] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    code: str
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    billing_type: str
    breakfast_price: Decimal
    lunch_price: Decimal
    dinner_price: Decimal
    supper_price: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MealRegistrationCreate(BaseModel):
    customer_id: int
    meal_date: date
    breakfast_count: int = 0
    breakfast_amount: Optional[Decimal] = None
    lunch_count: int = 0
    lunch_amount: Optional[Decimal] = None
    dinner_count: int = 0
    dinner_amount: Optional[Decimal] = None
    supper_count: int = 0
    supper_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class MealRegistrationUpdate(BaseModel):
    breakfast_count: Optional[int] = None
    breakfast_amount: Optional[Decimal] = None
    lunch_count: Optional[int] = None
    lunch_amount: Optional[Decimal] = None
    dinner_count: Optional[int] = None
    dinner_amount: Optional[Decimal] = None
    supper_count: Optional[int] = None
    supper_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class MealRegistrationResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    meal_date: date
    breakfast_count: int
    breakfast_amount: Decimal
    lunch_count: int
    lunch_amount: Decimal
    dinner_count: int
    dinner_amount: Decimal
    supper_count: int
    supper_amount: Decimal
    daily_total: Decimal
    notes: Optional[str] = None
    month_closed: bool

    class Config:
        from_attributes = True


class CustomerSettlementResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    settlement_month: str
    total_breakfast_count: int
    total_lunch_count: int
    total_dinner_count: int
    total_supper_count: int
    total_amount: Decimal
    adjustment_amount: Decimal
    final_amount: Decimal
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SettlementGenerateRequest(BaseModel):
    month: str  # YYYY-MM


class SettlementUpdateRequest(BaseModel):
    adjustment_amount: Optional[Decimal] = None
    notes: Optional[str] = None
