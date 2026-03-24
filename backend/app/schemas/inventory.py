"""Inventory schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class InventoryTransactionItemCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    batch_no: Optional[str] = None


class InventoryTransactionCreate(BaseModel):
    transaction_type: str  # inbound, outbound, return_supplier, return_inbound, damage, loss, stocktake_adjust
    transaction_date: date
    supplier_id: Optional[int] = None
    customer_id: Optional[int] = None
    items: List[InventoryTransactionItemCreate]
    notes: Optional[str] = None


class InventoryTransactionItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    product_unit: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    batch_no: Optional[str] = None

    class Config:
        from_attributes = True


class InventoryTransactionResponse(BaseModel):
    id: int
    code: str
    transaction_type: str
    transaction_date: date
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    status: str
    total_amount: Decimal
    items: List[InventoryTransactionItemResponse] = []
    notes: Optional[str] = None
    month_closed: bool

    class Config:
        from_attributes = True


class InventoryStockResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    product_unit: Optional[str] = None
    category_name: Optional[str] = None
    current_qty: Decimal
    avg_unit_cost: Decimal
    last_inbound_date: Optional[date] = None
    last_outbound_date: Optional[date] = None

    class Config:
        from_attributes = True
