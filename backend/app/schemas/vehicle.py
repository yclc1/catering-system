"""Vehicle schemas."""
from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class VehicleCreate(BaseModel):
    plate_number: str
    brand: Optional[str] = None
    model: Optional[str] = None
    vin: Optional[str] = None
    purchase_date: Optional[date] = None
    insurance_expiry_date: Optional[date] = None
    insurance_company: Optional[str] = None
    insurance_policy_no: Optional[str] = None
    annual_inspection_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    maintenance_interval_km: Optional[int] = None
    current_mileage: Optional[int] = None
    assigned_driver: Optional[str] = None
    notes: Optional[str] = None


class VehicleUpdate(BaseModel):
    plate_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    insurance_expiry_date: Optional[date] = None
    insurance_company: Optional[str] = None
    next_maintenance_date: Optional[date] = None
    maintenance_interval_km: Optional[int] = None
    current_mileage: Optional[int] = None
    assigned_driver: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class VehicleResponse(BaseModel):
    id: int
    code: str
    plate_number: str
    brand: Optional[str] = None
    model: Optional[str] = None
    vin: Optional[str] = None
    purchase_date: Optional[date] = None
    insurance_expiry_date: Optional[date] = None
    insurance_company: Optional[str] = None
    insurance_policy_no: Optional[str] = None
    annual_inspection_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    maintenance_interval_km: Optional[int] = None
    current_mileage: Optional[int] = None
    assigned_driver: Optional[str] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MaintenanceRecordCreate(BaseModel):
    maintenance_type: str
    maintenance_date: date
    mileage_at_maintenance: Optional[int] = None
    cost: Decimal = Decimal("0")
    vendor: Optional[str] = None
    description: Optional[str] = None
    next_maintenance_date: Optional[date] = None


class MaintenanceRecordResponse(BaseModel):
    id: int
    vehicle_id: int
    maintenance_type: str
    maintenance_date: date
    mileage_at_maintenance: Optional[int] = None
    cost: Decimal
    vendor: Optional[str] = None
    description: Optional[str] = None
    next_maintenance_date: Optional[date] = None

    class Config:
        from_attributes = True


class InsuranceRecordCreate(BaseModel):
    insurance_type: str
    policy_no: Optional[str] = None
    company: Optional[str] = None
    start_date: date
    end_date: date
    premium: Decimal
    notes: Optional[str] = None


class InsuranceRecordResponse(BaseModel):
    id: int
    vehicle_id: int
    insurance_type: str
    policy_no: Optional[str] = None
    company: Optional[str] = None
    start_date: date
    end_date: date
    premium: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True
