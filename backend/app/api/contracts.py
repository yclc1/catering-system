"""Contract API."""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.contract import Contract, ContractReminder
from app.core.exceptions import NotFoundError
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractResponse,
    ContractReminderCreate, ContractReminderResponse,
)
from app.schemas import PageResponse, MessageResponse
from app.services import generate_code
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/contracts", tags=["合同管理"])


@router.get("", response_model=PageResponse[ContractResponse])
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Contract).where(Contract.is_deleted == False)
    count_query = select(func.count(Contract.id)).where(Contract.is_deleted == False)

    if keyword:
        query = query.where(Contract.title.ilike(f"%{keyword}%") | Contract.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(Contract.title.ilike(f"%{keyword}%") | Contract.code.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Contract.status == status)
        count_query = count_query.where(Contract.status == status)
    if contract_type:
        query = query.where(Contract.contract_type == contract_type)
        count_query = count_query.where(Contract.contract_type == contract_type)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Contract.id.desc()).offset((page - 1) * page_size).limit(page_size))
    contracts = result.scalars().all()

    items = [ContractResponse(
        id=c.id, code=c.code, title=c.title, contract_type=c.contract_type,
        counterparty_type=c.counterparty_type,
        customer_id=c.customer_id, customer_name=c.customer.name if c.customer else None,
        supplier_id=c.supplier_id, supplier_name=c.supplier.name if c.supplier else None,
        start_date=c.start_date, end_date=c.end_date, amount=c.amount,
        status=c.status, file_url=c.file_url, reminder_days_before=c.reminder_days_before,
        notes=c.notes,
    ) for c in contracts]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("", response_model=ContractResponse)
async def create_contract(data: ContractCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    code = await generate_code(db, "contract")
    contract = Contract(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(contract)
    await db.flush()

    # Auto-create expiry reminder
    from datetime import timedelta
    reminder_date = data.end_date - timedelta(days=data.reminder_days_before)
    reminder = ContractReminder(
        contract_id=contract.id,
        reminder_date=reminder_date,
        reminder_type="expiry",
        message=f"合同 [{data.title}] 将于 {data.end_date} 到期",
    )
    db.add(reminder)
    await db.flush()

    await create_audit_log(db, current_user.id, current_user.username, "create", "contract", resource_id=contract.id, resource_code=code)

    result = await db.execute(select(Contract).where(Contract.id == contract.id))
    c = result.scalar_one()
    return ContractResponse(
        id=c.id, code=c.code, title=c.title, contract_type=c.contract_type,
        counterparty_type=c.counterparty_type,
        customer_id=c.customer_id, customer_name=c.customer.name if c.customer else None,
        supplier_id=c.supplier_id, supplier_name=c.supplier.name if c.supplier else None,
        start_date=c.start_date, end_date=c.end_date, amount=c.amount,
        status=c.status, file_url=c.file_url, reminder_days_before=c.reminder_days_before,
        notes=c.notes,
    )


@router.get("/reminders")
async def contract_reminders(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date, timedelta
    today = date.today()
    threshold = today + timedelta(days=60)

    result = await db.execute(
        select(Contract).where(
            Contract.is_deleted == False,
            Contract.status == "active",
            Contract.end_date <= threshold,
        ).order_by(Contract.end_date)
    )
    contracts = result.scalars().all()

    reminders = []
    for c in contracts:
        days_left = (c.end_date - today).days
        reminders.append({
            "contract_id": c.id,
            "code": c.code,
            "title": c.title,
            "end_date": c.end_date.isoformat(),
            "days_left": days_left,
            "message": f"合同 [{c.title}] 将于 {c.end_date} 到期 (还剩{days_left}天)",
            "urgent": days_left <= 7,
        })
    return reminders


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Contract).where(Contract.id == contract_id, Contract.is_deleted == False))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("合同", contract_id)
    return ContractResponse(
        id=c.id, code=c.code, title=c.title, contract_type=c.contract_type,
        counterparty_type=c.counterparty_type,
        customer_id=c.customer_id, customer_name=c.customer.name if c.customer else None,
        supplier_id=c.supplier_id, supplier_name=c.supplier.name if c.supplier else None,
        start_date=c.start_date, end_date=c.end_date, amount=c.amount,
        status=c.status, file_url=c.file_url, reminder_days_before=c.reminder_days_before,
        notes=c.notes,
    )


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(contract_id: int, data: ContractUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Contract).where(Contract.id == contract_id, Contract.is_deleted == False))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("合同", contract_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    c.updated_by = current_user.id
    await db.flush()

    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    c = result.scalar_one()
    return ContractResponse(
        id=c.id, code=c.code, title=c.title, contract_type=c.contract_type,
        counterparty_type=c.counterparty_type,
        customer_id=c.customer_id, customer_name=c.customer.name if c.customer else None,
        supplier_id=c.supplier_id, supplier_name=c.supplier.name if c.supplier else None,
        start_date=c.start_date, end_date=c.end_date, amount=c.amount,
        status=c.status, file_url=c.file_url, reminder_days_before=c.reminder_days_before,
        notes=c.notes,
    )


@router.delete("/{contract_id}", response_model=MessageResponse)
async def delete_contract(contract_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Contract).where(Contract.id == contract_id, Contract.is_deleted == False))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("合同", contract_id)
    c.is_deleted = True
    c.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="合同已删除")


# --- Reminders CRUD ---

@router.post("/{contract_id}/reminders", response_model=ContractReminderResponse)
async def add_reminder(contract_id: int, data: ContractReminderCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    reminder = ContractReminder(contract_id=contract_id, **data.model_dump())
    db.add(reminder)
    await db.flush()
    return ContractReminderResponse.model_validate(reminder)


@router.delete("/{contract_id}/reminders/{reminder_id}", response_model=MessageResponse)
async def delete_reminder(contract_id: int, reminder_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ContractReminder).where(ContractReminder.id == reminder_id, ContractReminder.contract_id == contract_id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise NotFoundError("提醒", reminder_id)
    await db.delete(reminder)
    return MessageResponse(message="提醒已删除")
