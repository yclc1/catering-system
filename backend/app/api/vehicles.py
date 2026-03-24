"""Vehicle API."""
from typing import Optional
from datetime import datetime, timezone, date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleMaintenanceRecord, VehicleInsuranceRecord
from app.core.exceptions import NotFoundError
from app.schemas.vehicle import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    MaintenanceRecordCreate, MaintenanceRecordResponse,
    InsuranceRecordCreate, InsuranceRecordResponse,
)
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.services import generate_code
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/vehicles", tags=["车辆管理"])


@router.get("", response_model=PageResponse[VehicleResponse])
async def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Vehicle).where(Vehicle.is_deleted == False)
    count_query = select(func.count(Vehicle.id)).where(Vehicle.is_deleted == False)

    if keyword:
        query = query.where(Vehicle.plate_number.ilike(f"%{keyword}%") | Vehicle.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(Vehicle.plate_number.ilike(f"%{keyword}%") | Vehicle.code.ilike(f"%{keyword}%"))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Vehicle.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [VehicleResponse.model_validate(v) for v in result.scalars().all()]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("", response_model=VehicleResponse)
async def create_vehicle(data: VehicleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    code = await generate_code(db, "vehicle")
    vehicle = Vehicle(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(vehicle)
    await db.flush()
    await create_audit_log(db, current_user.id, current_user.username, "create", "vehicle", resource_id=vehicle.id, resource_code=code)
    return VehicleResponse.model_validate(vehicle)


@router.get("/reminders")
async def vehicle_reminders(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get upcoming insurance and maintenance reminders."""
    today = date.today()
    threshold = today + timedelta(days=30)

    result = await db.execute(
        select(Vehicle).where(
            Vehicle.is_deleted == False,
            or_(
                Vehicle.insurance_expiry_date <= threshold,
                Vehicle.next_maintenance_date <= threshold,
            ),
        ).order_by(Vehicle.insurance_expiry_date)
    )
    vehicles = result.scalars().all()

    reminders = []
    for v in vehicles:
        if v.insurance_expiry_date and v.insurance_expiry_date <= threshold:
            days_left = (v.insurance_expiry_date - today).days
            reminders.append({
                "type": "insurance",
                "vehicle_id": v.id,
                "plate_number": v.plate_number,
                "date": v.insurance_expiry_date.isoformat(),
                "days_left": days_left,
                "message": f"车辆 {v.plate_number} 保险将于 {v.insurance_expiry_date} 到期 (还剩{days_left}天)",
                "urgent": days_left <= 7,
            })
        if v.next_maintenance_date and v.next_maintenance_date <= threshold:
            days_left = (v.next_maintenance_date - today).days
            reminders.append({
                "type": "maintenance",
                "vehicle_id": v.id,
                "plate_number": v.plate_number,
                "date": v.next_maintenance_date.isoformat(),
                "days_left": days_left,
                "message": f"车辆 {v.plate_number} 需于 {v.next_maintenance_date} 前保养 (还剩{days_left}天)",
                "urgent": days_left <= 7,
            })

    return sorted(reminders, key=lambda x: x["days_left"])


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.is_deleted == False))
    v = result.scalar_one_or_none()
    if not v:
        raise NotFoundError("车辆", vehicle_id)
    return VehicleResponse.model_validate(v)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: int, data: VehicleUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.is_deleted == False))
    v = result.scalar_one_or_none()
    if not v:
        raise NotFoundError("车辆", vehicle_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(v, field, value)
    v.updated_by = current_user.id
    await db.flush()
    return VehicleResponse.model_validate(v)


@router.delete("/{vehicle_id}", response_model=MessageResponse)
async def delete_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.is_deleted == False))
    v = result.scalar_one_or_none()
    if not v:
        raise NotFoundError("车辆", vehicle_id)
    v.is_deleted = True
    v.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="车辆已删除")


# --- Maintenance ---

@router.get("/{vehicle_id}/maintenance", response_model=list[MaintenanceRecordResponse])
async def list_maintenance(vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(VehicleMaintenanceRecord).where(VehicleMaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(VehicleMaintenanceRecord.maintenance_date.desc())
    )
    return [MaintenanceRecordResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/{vehicle_id}/maintenance", response_model=MaintenanceRecordResponse)
async def create_maintenance(vehicle_id: int, data: MaintenanceRecordCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = VehicleMaintenanceRecord(vehicle_id=vehicle_id, **data.model_dump(), created_by=current_user.id)
    db.add(record)
    # Update vehicle next maintenance date
    if data.next_maintenance_date:
        v_result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
        vehicle = v_result.scalar_one()
        vehicle.next_maintenance_date = data.next_maintenance_date
        if data.mileage_at_maintenance:
            vehicle.current_mileage = data.mileage_at_maintenance
    await db.flush()
    return MaintenanceRecordResponse.model_validate(record)


# --- Insurance ---

@router.get("/{vehicle_id}/insurance", response_model=list[InsuranceRecordResponse])
async def list_insurance(vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(VehicleInsuranceRecord).where(VehicleInsuranceRecord.vehicle_id == vehicle_id)
        .order_by(VehicleInsuranceRecord.end_date.desc())
    )
    return [InsuranceRecordResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/{vehicle_id}/insurance", response_model=InsuranceRecordResponse)
async def create_insurance(vehicle_id: int, data: InsuranceRecordCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = VehicleInsuranceRecord(vehicle_id=vehicle_id, **data.model_dump(), created_by=current_user.id)
    db.add(record)
    # Update vehicle insurance expiry
    v_result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = v_result.scalar_one()
    vehicle.insurance_expiry_date = data.end_date
    vehicle.insurance_company = data.company
    vehicle.insurance_policy_no = data.policy_no
    await db.flush()
    return InsuranceRecordResponse.model_validate(record)
