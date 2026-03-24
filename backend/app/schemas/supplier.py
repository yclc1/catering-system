"""Supplier schemas."""
from typing import Optional
from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


class SupplierResponse(BaseModel):
    id: int
    code: str
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
