"""Payment Account and Record API."""
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.account import PaymentAccount, PaymentRecord
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.account import (
    PaymentAccountCreate, PaymentAccountUpdate, PaymentAccountResponse,
    PaymentRecordCreate, PaymentRecordUpdate, PaymentRecordResponse,
)
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.services import generate_code
from app.services.audit_service import create_audit_log
from app.services.monthly_close_service import check_month_not_closed

router = APIRouter(prefix="/accounts", tags=["账户管理"])
payment_router = APIRouter(prefix="/payments", tags=["收付款管理"])


# --- Accounts ---

@router.get("", response_model=list[PaymentAccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentAccount).where(PaymentAccount.is_deleted == False).order_by(PaymentAccount.id))
    return [PaymentAccountResponse.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=PaymentAccountResponse)
async def create_account(data: PaymentAccountCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    code = await generate_code(db, "account")
    account = PaymentAccount(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(account)
    await db.flush()
    return PaymentAccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=PaymentAccountResponse)
async def update_account(account_id: int, data: PaymentAccountUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == account_id, PaymentAccount.is_deleted == False))
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError("账户", account_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    account.updated_by = current_user.id
    await db.flush()
    return PaymentAccountResponse.model_validate(account)


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == account_id, PaymentAccount.is_deleted == False))
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError("账户", account_id)
    account.is_deleted = True
    account.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="账户已删除")


@router.get("/dropdown", response_model=list[DropdownItem])
async def account_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentAccount).where(PaymentAccount.is_deleted == False, PaymentAccount.is_active == True))
    return [DropdownItem(id=a.id, name=a.name, code=a.code) for a in result.scalars().all()]


# --- Payment Records ---

@payment_router.get("", response_model=PageResponse[PaymentRecordResponse])
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    direction: Optional[str] = None,
    counterparty_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PaymentRecord)
    count_query = select(func.count(PaymentRecord.id))

    if direction:
        query = query.where(PaymentRecord.direction == direction)
        count_query = count_query.where(PaymentRecord.direction == direction)
    if counterparty_type:
        query = query.where(PaymentRecord.counterparty_type == counterparty_type)
        count_query = count_query.where(PaymentRecord.counterparty_type == counterparty_type)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(PaymentRecord.id.desc()).offset((page - 1) * page_size).limit(page_size))
    records = result.scalars().all()

    items = [PaymentRecordResponse(
        id=r.id, code=r.code, account_id=r.account_id,
        account_name=r.account.name if r.account else None,
        direction=r.direction, amount=r.amount, payment_date=r.payment_date,
        counterparty_type=r.counterparty_type,
        customer_id=r.customer_id, customer_name=r.customer.name if r.customer else None,
        supplier_id=r.supplier_id, supplier_name=r.supplier.name if r.supplier else None,
        payment_method=r.payment_method, reference_no=r.reference_no,
        notes=r.notes, month_closed=r.month_closed,
    ) for r in records]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@payment_router.post("", response_model=PaymentRecordResponse)
async def create_payment(data: PaymentRecordCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await check_month_not_closed(db, data.payment_date)

    code = await generate_code(db, "payment_record")
    record = PaymentRecord(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(record)
    await db.flush()

    # Update account balance
    account_result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == data.account_id).with_for_update())
    account = account_result.scalar_one()
    if data.direction == "inbound":
        account.current_balance += data.amount
    else:
        new_balance = account.current_balance - data.amount
        if new_balance < 0:
            raise BusinessError(f"账户余额不足，当前余额: {account.current_balance}")
        account.current_balance = new_balance

    await create_audit_log(db, current_user.id, current_user.username, "create", "payment_record", resource_id=record.id, resource_code=code)
    await db.flush()

    result = await db.execute(select(PaymentRecord).where(PaymentRecord.id == record.id))
    r = result.scalar_one()
    return PaymentRecordResponse(
        id=r.id, code=r.code, account_id=r.account_id,
        account_name=r.account.name if r.account else None,
        direction=r.direction, amount=r.amount, payment_date=r.payment_date,
        counterparty_type=r.counterparty_type,
        customer_id=r.customer_id, customer_name=r.customer.name if r.customer else None,
        supplier_id=r.supplier_id, supplier_name=r.supplier.name if r.supplier else None,
        payment_method=r.payment_method, reference_no=r.reference_no,
        notes=r.notes, month_closed=r.month_closed,
    )


@payment_router.put("/{record_id}", response_model=PaymentRecordResponse)
async def update_payment(record_id: int, data: PaymentRecordUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentRecord).where(PaymentRecord.id == record_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("收付款记录", record_id)
    if r.month_closed:
        raise BusinessError("该记录所在月份已关账，无法修改")

    old_amount = r.amount
    old_account_id = r.account_id

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(r, field, value)
    r.updated_by = current_user.id

    # Handle account change
    if data.account_id is not None and data.account_id != old_account_id:
        # Revert old account
        old_account_result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == old_account_id).with_for_update())
        old_account = old_account_result.scalar_one()
        if r.direction == "inbound":
            old_account.current_balance -= old_amount
        else:
            old_account.current_balance += old_amount

        # Update new account
        new_account_result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == data.account_id).with_for_update())
        new_account = new_account_result.scalar_one()
        if r.direction == "inbound":
            new_account.current_balance += r.amount
        else:
            new_account.current_balance -= r.amount
    # Adjust account balance if amount changed
    elif data.amount is not None and data.amount != old_amount:
        account_result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == r.account_id).with_for_update())
        account = account_result.scalar_one()
        diff = data.amount - old_amount
        if r.direction == "inbound":
            account.current_balance += diff
        else:
            account.current_balance -= diff

    await create_audit_log(db, current_user.id, current_user.username, "update", "payment_record", resource_id=r.id, resource_code=r.code)
    await db.flush()

    result = await db.execute(select(PaymentRecord).where(PaymentRecord.id == record_id))
    r = result.scalar_one()
    return PaymentRecordResponse(
        id=r.id, code=r.code, account_id=r.account_id,
        account_name=r.account.name if r.account else None,
        direction=r.direction, amount=r.amount, payment_date=r.payment_date,
        counterparty_type=r.counterparty_type,
        customer_id=r.customer_id, customer_name=r.customer.name if r.customer else None,
        supplier_id=r.supplier_id, supplier_name=r.supplier.name if r.supplier else None,
        payment_method=r.payment_method, reference_no=r.reference_no,
        notes=r.notes, month_closed=r.month_closed,
    )


@payment_router.delete("/{record_id}", response_model=MessageResponse)
async def delete_payment(record_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentRecord).where(PaymentRecord.id == record_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("收付款记录", record_id)
    if r.month_closed:
        raise BusinessError("该记录所在月份已关账，无法删除")

    # Reverse account balance
    account_result = await db.execute(select(PaymentAccount).where(PaymentAccount.id == r.account_id).with_for_update())
    account = account_result.scalar_one()
    if r.direction == "inbound":
        account.current_balance -= r.amount
    else:
        account.current_balance += r.amount

    await create_audit_log(db, current_user.id, current_user.username, "delete", "payment_record", resource_id=r.id, resource_code=r.code)
    r.is_deleted = True
    r.updated_by = current_user.id
    await db.flush()
    return MessageResponse(message="收付款记录已删除")


@payment_router.get("/{record_id}", response_model=PaymentRecordResponse)
async def get_payment(record_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PaymentRecord).where(PaymentRecord.id == record_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("收付款记录", record_id)
    return PaymentRecordResponse(
        id=r.id, code=r.code, account_id=r.account_id,
        account_name=r.account.name if r.account else None,
        direction=r.direction, amount=r.amount, payment_date=r.payment_date,
        counterparty_type=r.counterparty_type,
        customer_id=r.customer_id, customer_name=r.customer.name if r.customer else None,
        supplier_id=r.supplier_id, supplier_name=r.supplier.name if r.supplier else None,
        payment_method=r.payment_method, reference_no=r.reference_no,
        notes=r.notes, month_closed=r.month_closed,
    )
