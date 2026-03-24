"""Vehicle models."""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Vehicle(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    plate_number = Column(String(16), unique=True, nullable=False, index=True)
    brand = Column(String(64))
    model = Column(String(64))
    vin = Column(String(32))
    purchase_date = Column(Date)
    insurance_expiry_date = Column(Date, index=True)
    insurance_company = Column(String(128))
    insurance_policy_no = Column(String(64))
    annual_inspection_date = Column(Date)
    next_maintenance_date = Column(Date, index=True)
    maintenance_interval_km = Column(Integer)
    current_mileage = Column(Integer)
    assigned_driver = Column(String(64))
    status = Column(String(16), nullable=False, default="active")
    notes = Column(Text)

    maintenance_records = relationship("VehicleMaintenanceRecord", back_populates="vehicle", lazy="dynamic")
    insurance_records = relationship("VehicleInsuranceRecord", back_populates="vehicle", lazy="dynamic")


class VehicleMaintenanceRecord(AuditMixin, Base):
    __tablename__ = "vehicle_maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    maintenance_type = Column(String(32), nullable=False)
    maintenance_date = Column(Date, nullable=False)
    mileage_at_maintenance = Column(Integer)
    cost = Column(Numeric(12, 2), nullable=False, default=0)
    vendor = Column(String(128))
    description = Column(Text)
    next_maintenance_date = Column(Date)

    vehicle = relationship("Vehicle", back_populates="maintenance_records")


class VehicleInsuranceRecord(AuditMixin, Base):
    __tablename__ = "vehicle_insurance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    insurance_type = Column(String(32), nullable=False)
    policy_no = Column(String(64))
    company = Column(String(128))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    premium = Column(Numeric(12, 2), nullable=False)
    notes = Column(Text)

    vehicle = relationship("Vehicle", back_populates="insurance_records")
