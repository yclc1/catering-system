"""Customer API - CRUD, meal registration, settlement."""
from typing import Optional
from datetime import datetime, timezone, date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.customer import Customer, MealRegistration, CustomerSettlement
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    MealRegistrationCreate, MealRegistrationUpdate, MealRegistrationResponse,
    CustomerSettlementResponse, SettlementGenerateRequest, SettlementUpdateRequest,
)
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.services import generate_code
from app.services.audit_service import create_audit_log
from app.services.monthly_close_service import check_month_not_closed

router = APIRouter(prefix="/customers", tags=["客户管理"])


@router.get("", response_model=PageResponse[CustomerResponse])
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Customer).where(Customer.is_deleted == False)
    count_query = select(func.count(Customer.id)).where(Customer.is_deleted == False)

    if keyword:
        query = query.where(Customer.name.ilike(f"%{keyword}%") | Customer.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(Customer.name.ilike(f"%{keyword}%") | Customer.code.ilike(f"%{keyword}%"))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [CustomerResponse.model_validate(c) for c in result.scalars().all()]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("", response_model=CustomerResponse)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    code = await generate_code(db, "customer")
    customer = Customer(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(customer)
    await db.flush()
    await create_audit_log(db, current_user.id, current_user.username, "create", "customer", resource_id=customer.id, resource_code=code)
    return CustomerResponse.model_validate(customer)


@router.get("/dropdown", response_model=list[DropdownItem])
async def customer_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.is_deleted == False).order_by(Customer.name))
    return [DropdownItem(id=c.id, name=c.name, code=c.code) for c in result.scalars().all()]


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户", customer_id)
    return CustomerResponse.model_validate(c)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, data: CustomerUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户", customer_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    c.updated_by = current_user.id
    await db.flush()
    return CustomerResponse.model_validate(c)


@router.delete("/{customer_id}", response_model=MessageResponse)
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户", customer_id)
    c.is_deleted = True
    c.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="客户已删除")


# --- Meal Registration ---

@router.get("/{customer_id}/meals", response_model=PageResponse[MealRegistrationResponse])
async def list_meals(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(31, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(MealRegistration).where(MealRegistration.customer_id == customer_id)
    count_query = select(func.count(MealRegistration.id)).where(MealRegistration.customer_id == customer_id)

    if start_date:
        query = query.where(MealRegistration.meal_date >= start_date)
        count_query = count_query.where(MealRegistration.meal_date >= start_date)
    if end_date:
        query = query.where(MealRegistration.meal_date <= end_date)
        count_query = count_query.where(MealRegistration.meal_date <= end_date)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(MealRegistration.meal_date.desc()).offset((page - 1) * page_size).limit(page_size))
    meals = result.scalars().all()

    items = [MealRegistrationResponse(
        id=m.id, customer_id=m.customer_id,
        customer_name=m.customer.name if m.customer else None,
        meal_date=m.meal_date,
        breakfast_count=m.breakfast_count, breakfast_amount=m.breakfast_amount,
        lunch_count=m.lunch_count, lunch_amount=m.lunch_amount,
        dinner_count=m.dinner_count, dinner_amount=m.dinner_amount,
        supper_count=m.supper_count, supper_amount=m.supper_amount,
        daily_total=m.daily_total, notes=m.notes, month_closed=m.month_closed,
    ) for m in meals]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("/{customer_id}/meals", response_model=MealRegistrationResponse)
async def create_meal(
    customer_id: int, data: MealRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await check_month_not_closed(db, data.meal_date)

    # Check duplicate
    existing = await db.execute(
        select(MealRegistration).where(
            MealRegistration.customer_id == customer_id,
            MealRegistration.meal_date == data.meal_date,
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateError(f"该客户在 {data.meal_date} 已有餐次登记")

    # Get customer prices
    cust_result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", customer_id)

    # Calculate amounts: use provided amount or count * price
    breakfast_amount = data.breakfast_amount if data.breakfast_amount is not None else Decimal(str(data.breakfast_count)) * customer.breakfast_price
    lunch_amount = data.lunch_amount if data.lunch_amount is not None else Decimal(str(data.lunch_count)) * customer.lunch_price
    dinner_amount = data.dinner_amount if data.dinner_amount is not None else Decimal(str(data.dinner_count)) * customer.dinner_price
    supper_amount = data.supper_amount if data.supper_amount is not None else Decimal(str(data.supper_count)) * customer.supper_price
    daily_total = breakfast_amount + lunch_amount + dinner_amount + supper_amount

    meal = MealRegistration(
        customer_id=customer_id,
        meal_date=data.meal_date,
        breakfast_count=data.breakfast_count, breakfast_amount=breakfast_amount,
        lunch_count=data.lunch_count, lunch_amount=lunch_amount,
        dinner_count=data.dinner_count, dinner_amount=dinner_amount,
        supper_count=data.supper_count, supper_amount=supper_amount,
        daily_total=daily_total,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(meal)
    await db.flush()

    return MealRegistrationResponse(
        id=meal.id, customer_id=meal.customer_id, customer_name=customer.name,
        meal_date=meal.meal_date,
        breakfast_count=meal.breakfast_count, breakfast_amount=meal.breakfast_amount,
        lunch_count=meal.lunch_count, lunch_amount=meal.lunch_amount,
        dinner_count=meal.dinner_count, dinner_amount=meal.dinner_amount,
        supper_count=meal.supper_count, supper_amount=meal.supper_amount,
        daily_total=meal.daily_total, notes=meal.notes, month_closed=meal.month_closed,
    )


@router.put("/{customer_id}/meals/{meal_id}", response_model=MealRegistrationResponse)
async def update_meal(
    customer_id: int, meal_id: int, data: MealRegistrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MealRegistration).where(MealRegistration.id == meal_id, MealRegistration.customer_id == customer_id)
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise NotFoundError("用餐记录", meal_id)
    if meal.month_closed:
        raise BusinessError("该月份已锁定，无法修改")

    await check_month_not_closed(db, meal.meal_date)

    # Get customer for price calculation
    cust_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = cust_result.scalar_one()

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(meal, field, value)

    # Recalculate amounts if counts changed
    if data.breakfast_count is not None and data.breakfast_amount is None:
        meal.breakfast_amount = Decimal(str(meal.breakfast_count)) * customer.breakfast_price
    if data.lunch_count is not None and data.lunch_amount is None:
        meal.lunch_amount = Decimal(str(meal.lunch_count)) * customer.lunch_price
    if data.dinner_count is not None and data.dinner_amount is None:
        meal.dinner_amount = Decimal(str(meal.dinner_count)) * customer.dinner_price
    if data.supper_count is not None and data.supper_amount is None:
        meal.supper_amount = Decimal(str(meal.supper_count)) * customer.supper_price

    meal.daily_total = meal.breakfast_amount + meal.lunch_amount + meal.dinner_amount + meal.supper_amount
    meal.updated_by = current_user.id
    await db.flush()

    return MealRegistrationResponse(
        id=meal.id, customer_id=meal.customer_id, customer_name=customer.name,
        meal_date=meal.meal_date,
        breakfast_count=meal.breakfast_count, breakfast_amount=meal.breakfast_amount,
        lunch_count=meal.lunch_count, lunch_amount=meal.lunch_amount,
        dinner_count=meal.dinner_count, dinner_amount=meal.dinner_amount,
        supper_count=meal.supper_count, supper_amount=meal.supper_amount,
        daily_total=meal.daily_total, notes=meal.notes, month_closed=meal.month_closed,
    )


@router.delete("/{customer_id}/meals/{meal_id}", response_model=MessageResponse)
async def delete_meal(
    customer_id: int, meal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MealRegistration).where(MealRegistration.id == meal_id, MealRegistration.customer_id == customer_id)
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise NotFoundError("用餐记录", meal_id)
    if meal.month_closed:
        raise BusinessError("该月份已锁定，无法删除")

    await db.delete(meal)
    return MessageResponse(message="用餐记录已删除")


# --- Settlement ---

@router.get("/{customer_id}/settlements", response_model=list[CustomerSettlementResponse])
async def list_settlements(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(CustomerSettlement)
        .where(CustomerSettlement.customer_id == customer_id)
        .order_by(CustomerSettlement.settlement_month.desc())
    )
    settlements = result.scalars().all()
    return [CustomerSettlementResponse(
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


@router.post("/{customer_id}/settlements/generate", response_model=CustomerSettlementResponse)
async def generate_settlement(
    customer_id: int, data: SettlementGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate monthly settlement from meal registration data."""
    # Parse month
    year, mon = int(data.month[:4]), int(data.month[5:7])
    start = date(year, mon, 1)
    if mon == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, mon + 1, 1)

    # Get customer
    cust_result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", customer_id)

    # Aggregate meal data
    result = await db.execute(
        select(
            func.coalesce(func.sum(MealRegistration.breakfast_count), 0),
            func.coalesce(func.sum(MealRegistration.lunch_count), 0),
            func.coalesce(func.sum(MealRegistration.dinner_count), 0),
            func.coalesce(func.sum(MealRegistration.supper_count), 0),
            func.coalesce(func.sum(MealRegistration.daily_total), 0),
        ).where(
            MealRegistration.customer_id == customer_id,
            MealRegistration.meal_date >= start,
            MealRegistration.meal_date < end,
        )
    )
    row = result.one()
    bc, lc, dc, sc, total = row

    # Check if settlement already exists with row lock
    existing = await db.execute(
        select(CustomerSettlement).where(
            CustomerSettlement.customer_id == customer_id,
            CustomerSettlement.settlement_month == data.month,
        ).with_for_update()
    )
    settlement = existing.scalar_one_or_none()

    if settlement:
        # Update existing
        settlement.total_breakfast_count = bc
        settlement.total_lunch_count = lc
        settlement.total_dinner_count = dc
        settlement.total_supper_count = sc
        settlement.total_amount = total
        settlement.final_amount = total + settlement.adjustment_amount
        settlement.updated_by = current_user.id
    else:
        settlement = CustomerSettlement(
            customer_id=customer_id,
            settlement_month=data.month,
            total_breakfast_count=bc,
            total_lunch_count=lc,
            total_dinner_count=dc,
            total_supper_count=sc,
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


@router.put("/{customer_id}/settlements/{settlement_id}", response_model=CustomerSettlementResponse)
async def update_settlement(
    customer_id: int, settlement_id: int, data: SettlementUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CustomerSettlement).where(
            CustomerSettlement.id == settlement_id,
            CustomerSettlement.customer_id == customer_id,
        )
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


@router.post("/{customer_id}/settlements/{settlement_id}/confirm", response_model=MessageResponse)
async def confirm_settlement(
    customer_id: int, settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CustomerSettlement).where(
            CustomerSettlement.id == settlement_id,
            CustomerSettlement.customer_id == customer_id,
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("结算记录", settlement_id)
    s.status = "confirmed"
    s.updated_by = current_user.id
    await create_audit_log(db, current_user.id, current_user.username, "confirm", "customer_settlement", resource_id=s.id)
    return MessageResponse(message="结算已确认")


@router.get("/{customer_id}/settlements/{settlement_id}/export")
async def export_settlement(
    customer_id: int, settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export settlement to Excel."""
    from app.services.excel_service import export_customer_settlement
    result = await db.execute(
        select(CustomerSettlement).where(
            CustomerSettlement.id == settlement_id,
            CustomerSettlement.customer_id == customer_id,
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("结算记录", settlement_id)

    # Get meal details
    year, mon = int(s.settlement_month[:4]), int(s.settlement_month[5:7])
    start = date(year, mon, 1)
    if mon == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, mon + 1, 1)

    meals_result = await db.execute(
        select(MealRegistration)
        .where(
            MealRegistration.customer_id == customer_id,
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
