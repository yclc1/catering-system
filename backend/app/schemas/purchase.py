"""Purchase schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    notes: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    order_date: date
    items: List[PurchaseOrderItemCreate]
    notes: Optional[str] = None


class PurchaseOrderItemUpdate(BaseModel):
    id: Optional[int] = None
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    notes: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[int] = None
    order_date: Optional[date] = None
    items: Optional[List[PurchaseOrderItemUpdate]] = None
    notes: Optional[str] = None


class PurchaseOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    product_unit: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PurchaseOrderResponse(BaseModel):
    id: int
    code: str
    supplier_id: int
    supplier_name: Optional[str] = None
    order_date: date
    status: str
    total_amount: Decimal
    items: List[PurchaseOrderItemResponse] = []
    notes: Optional[str] = None
    month_closed: bool

    class Config:
        from_attributes = True
