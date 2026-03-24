"""Meal Registration API - flat paths for frontend compatibility."""
from typing import Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.customer import Customer, MealRegistration
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.customer import (
    MealRegistrationCreate, MealRegistrationUpdate, MealRegistrationResponse,
)
from app.schemas import PageResponse, MessageResponse
from app.services.monthly_close_service import check_month_not_closed

router = APIRouter(prefix="/meals", tags=["用餐登记"])


@router.get("", response_model=PageResponse[MealRegistrationResponse])
async def list_meals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(MealRegistration)
    count_query = select(func.count(MealRegistration.id))

    if customer_id:
        query = query.where(MealRegistration.customer_id == customer_id)
        count_query = count_query.where(MealRegistration.customer_id == customer_id)
    if start_date:
        query = query.where(MealRegistration.meal_date >= start_date)
        count_query = count_query.where(MealRegistration.meal_date >= start_date)
    if end_date:
        query = query.where(MealRegistration.meal_date <= end_date)
        count_query = count_query.where(MealRegistration.meal_date <= end_date)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(MealRegistration.meal_date.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
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

    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=(total + page_size - 1) // page_size)


@router.post("", response_model=MealRegistrationResponse)
async def create_meal(
    data: MealRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await check_month_not_closed(db, data.meal_date)

    cust_result = await db.execute(
        select(Customer).where(Customer.id == data.customer_id, Customer.is_deleted == False)
    )
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", data.customer_id)

    breakfast_amount = data.breakfast_amount if data.breakfast_amount is not None else Decimal(str(data.breakfast_count)) * customer.breakfast_price
    lunch_amount = data.lunch_amount if data.lunch_amount is not None else Decimal(str(data.lunch_count)) * customer.lunch_price
    dinner_amount = data.dinner_amount if data.dinner_amount is not None else Decimal(str(data.dinner_count)) * customer.dinner_price
    supper_amount = data.supper_amount if data.supper_amount is not None else Decimal(str(data.supper_count)) * customer.supper_price
    daily_total = breakfast_amount + lunch_amount + dinner_amount + supper_amount

    meal = MealRegistration(
        customer_id=data.customer_id,
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


@router.put("/{meal_id}", response_model=MealRegistrationResponse)
async def update_meal(
    meal_id: int, data: MealRegistrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MealRegistration).where(MealRegistration.id == meal_id))
    meal = result.scalar_one_or_none()
    if not meal:
        raise NotFoundError("用餐记录", meal_id)
    if meal.month_closed:
        raise BusinessError("该月份已锁定，无法修改")

    await check_month_not_closed(db, meal.meal_date)

    cust_result = await db.execute(select(Customer).where(Customer.id == meal.customer_id))
    customer = cust_result.scalar_one()

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(meal, field, value)

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


@router.delete("/{meal_id}", response_model=MessageResponse)
async def delete_meal(
    meal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MealRegistration).where(MealRegistration.id == meal_id))
    meal = result.scalar_one_or_none()
    if not meal:
        raise NotFoundError("用餐记录", meal_id)
    if meal.month_closed:
        raise BusinessError("该月份已锁定，无法删除")

    await db.delete(meal)
    return MessageResponse(message="用餐记录已删除")
