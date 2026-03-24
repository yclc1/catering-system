"""Product schemas."""
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal


class ProductCategoryCreate(BaseModel):
    name: str
    sort_order: int = 0


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    category_id: int
    unit: str
    spec: Optional[str] = None
    default_supplier_id: Optional[int] = None
    notes: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    unit: Optional[str] = None
    spec: Optional[str] = None
    default_supplier_id: Optional[int] = None
    notes: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    code: str
    name: str
    category_id: int
    category_name: Optional[str] = None
    unit: str
    spec: Optional[str] = None
    default_supplier_id: Optional[int] = None
    default_supplier_name: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PriceHistoryItem(BaseModel):
    date: str
    unit_price: Decimal
    supplier_name: Optional[str] = None
