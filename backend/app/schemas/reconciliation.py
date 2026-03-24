"""Reconciliation schemas."""
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel


class ReconciliationGenerateRequest(BaseModel):
    supplier_id: int
    month: str  # YYYY-MM


class ReconciliationUpdateRequest(BaseModel):
    notes: Optional[str] = None


class SupplierReconciliationResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    reconciliation_month: str
    total_inbound_amount: Decimal
    total_return_amount: Decimal
    net_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True
