"""Customer Settlement API - flat paths for frontend compatibility."""
from typing import Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.customer import Customer, MealRegistration, CustomerSettlement
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.customer import (
    CustomerSettlementResponse, SettlementGenerateRequest, SettlementUpdateRequest,
)
from app.schemas import PageResponse, MessageResponse
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/settlements", tags=["客户结算"])


@router.get("", response_model=PageResponse[CustomerSettlementResponse])
async def list_settlements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    month: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(CustomerSettlement)
    count_query = select(func.count(CustomerSettlement.id))

    if customer_id:
        query = query.where(CustomerSettlement.customer_id == customer_id)
        count_query = count_query.where(CustomerSettlement.customer_id == customer_id)
    if month:
        query = query.where(CustomerSettlement.settlement_month == month)
        count_query = count_query.where(CustomerSettlement.settlement_month == month)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(CustomerSettlement.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    settlements = result.scalars().all()

    items = [CustomerSettlementResponse(
        id=s.id, customer_id=s.customer_id,
        customer_name=s.customer.name if s.customer else None,
        settlement_month=s.settlement_month,
        total_breakfast_count=s.total_breakfast_count,
        total_lunch_count=s.total_lunch_count,
        total_dinner_count=s.total_dinner_count,
        total_supper_count=s.total_supper_count,
        total_amount=s.total_amount,
        adjustment_amount=s.adjustment_amount,
        final_amount=s.final_amount,
        status=s.status, notes=s.notes,
    ) for s in settlements]

    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=(total + page_size - 1) // page_size)


class SettlementGenerateFlat(SettlementGenerateRequest):
    customer_id: int


@router.post("/generate", response_model=CustomerSettlementResponse)
async def generate_settlement(
    data: SettlementGenerateFlat,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    year, mon = int(data.month[:4]), int(data.month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    cust_result = await db.execute(
        select(Customer).where(Customer.id == data.customer_id, Customer.is_deleted == False)
    )
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", data.customer_id)

    result = await db.execute(
        select(
            func.coalesce(func.sum(MealRegistration.breakfast_count), 0),
            func.coalesce(func.sum(MealRegistration.lunch_count), 0),
            func.coalesce(func.sum(MealRegistration.dinner_count), 0),
            func.coalesce(func.sum(MealRegistration.supper_count), 0),
            func.coalesce(func.sum(MealRegistration.daily_total), 0),
        ).where(
            MealRegistration.customer_id == data.customer_id,
            MealRegistration.meal_date >= start,
            MealRegistration.meal_date < end,
        )
    )
    row = result.one()
    bc, lc, dc, sc, total = row
    total = total or Decimal("0")

    existing = await db.execute(
        select(CustomerSettlement).where(
            CustomerSettlement.customer_id == data.customer_id,
            CustomerSettlement.settlement_month == data.month,
        )
    )
    settlement = existing.scalar_one_or_none()

    if settlement:
        settlement.total_breakfast_count = bc
        settlement.total_lunch_count = lc
        settlement.total_dinner_count = dc
        settlement.total_supper_count = sc
        settlement.total_amount = total
        settlement.final_amount = total + settlement.adjustment_amount
        settlement.updated_by = current_user.id
    else:
        settlement = CustomerSettlement(
            customer_id=data.customer_id,
            settlement_month=data.month,
            total_breakfast_count=bc, total_lunch_count=lc,
            total_dinner_count=dc, total_supper_count=sc,
            total_amount=total,
            adjustment_amount=Decimal("0"),
            final_amount=total,
            created_by=current_user.id,
        )
        db.add(settlement)

    await db.flush()
    return CustomerSettlementResponse(
        id=settlement.id, customer_id=settlement.customer_id, customer_name=customer.name,
        settlement_month=settlement.settlement_month,
        total_breakfast_count=settlement.total_breakfast_count,
        total_lunch_count=settlement.total_lunch_count,
        total_dinner_count=settlement.total_dinner_count,
        total_supper_count=settlement.total_supper_count,
        total_amount=settlement.total_amount,
        adjustment_amount=settlement.adjustment_amount,
        final_amount=settlement.final_amount,
        status=settlement.status, notes=settlement.notes,
    )


@router.put("/{settlement_id}", response_model=CustomerSettlementResponse)
async def update_settlement(
    settlement_id: int, data: SettlementUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CustomerSettlement).where(CustomerSettlement.id == settlement_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("结算记录", settlement_id)

    if data.adjustment_amount is not None:
        s.adjustment_amount = data.adjustment_amount
        s.final_amount = s.total_amount + data.adjustment_amount
    if data.notes is not None:
        s.notes = data.notes
    s.updated_by = current_user.id
    await db.flush()

    return CustomerSettlementResponse(
        id=s.id, customer_id=s.customer_id,
        customer_name=s.customer.name if s.customer else None,
        settlement_month=s.settlement_month,
        total_breakfast_count=s.total_breakfast_count,
        total_lunch_count=s.total_lunch_count,
        total_dinner_count=s.total_dinner_count,
        total_supper_count=s.total_supper_count,
        total_amount=s.total_amount,
        adjustment_amount=s.adjustment_amount,
        final_amount=s.final_amount,
        status=s.status, notes=s.notes,
    )


@router.post("/{settlement_id}/confirm", response_model=MessageResponse)
async def confirm_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CustomerSettlement).where(CustomerSettlement.id == settlement_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("结算记录", settlement_id)
    s.status = "confirmed"
    s.updated_by = current_user.id
    await create_audit_log(db, current_user.id, current_user.username, "confirm", "customer_settlement", resource_id=s.id)
    return MessageResponse(message="结算已确认")


@router.get("/{settlement_id}/export")
async def export_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.excel_service import export_customer_settlement

    result = await db.execute(
        select(CustomerSettlement).where(CustomerSettlement.id == settlement_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("结算记录", settlement_id)

    year, mon = int(s.settlement_month[:4]), int(s.settlement_month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    meals_result = await db.execute(
        select(MealRegistration)
        .where(
            MealRegistration.customer_id == s.customer_id,
            MealRegistration.meal_date >= start,
            MealRegistration.meal_date < end,
        )
        .order_by(MealRegistration.meal_date)
    )
    meals = meals_result.scalars().all()

    customer_name = s.customer.name if s.customer else "未知客户"
    output = export_customer_settlement(customer_name, s, meals)

    await create_audit_log(db, current_user.id, current_user.username, "export", "customer_settlement", resource_id=s.id)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=settlement_{customer_name}_{s.settlement_month}.xlsx"},
    )
