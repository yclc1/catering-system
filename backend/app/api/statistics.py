"""Statistics API."""
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.customer import CustomerSettlement, MealRegistration
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.inventory import InventoryTransactionItem, InventoryTransaction
from app.models.product import Product, ProductCategory
from app.models.account import PaymentRecord

router = APIRouter(prefix="/statistics", tags=["统计分析"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Dashboard aggregates."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Monthly sales (customer settlements)
    sales_result = await db.execute(
        select(func.coalesce(func.sum(CustomerSettlement.final_amount), 0))
        .where(CustomerSettlement.settlement_month == today.strftime("%Y-%m"))
    )
    monthly_sales = sales_result.scalar()

    # Monthly purchases
    purchase_result = await db.execute(
        select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0))
        .where(
            PurchaseOrder.status == "confirmed",
            PurchaseOrder.order_date >= month_start,
        )
    )
    monthly_purchases = purchase_result.scalar()

    # Monthly income
    income_result = await db.execute(
        select(func.coalesce(func.sum(PaymentRecord.amount), 0))
        .where(
            PaymentRecord.direction == "inbound",
            PaymentRecord.payment_date >= month_start,
        )
    )
    monthly_income = income_result.scalar()

    # Monthly expense payments
    expense_result = await db.execute(
        select(func.coalesce(func.sum(PaymentRecord.amount), 0))
        .where(
            PaymentRecord.direction == "outbound",
            PaymentRecord.payment_date >= month_start,
        )
    )
    monthly_expenses = expense_result.scalar()

    # Today's meal count
    today_meals = await db.execute(
        select(
            func.coalesce(func.sum(MealRegistration.breakfast_count), 0),
            func.coalesce(func.sum(MealRegistration.lunch_count), 0),
            func.coalesce(func.sum(MealRegistration.dinner_count), 0),
            func.coalesce(func.sum(MealRegistration.supper_count), 0),
        ).where(MealRegistration.meal_date == today)
    )
    bc, lc, dc, sc = today_meals.one()

    return {
        "monthly_sales": float(monthly_sales),
        "monthly_purchases": float(monthly_purchases),
        "monthly_income": float(monthly_income),
        "monthly_expenses": float(monthly_expenses),
        "today_meals": {
            "breakfast": bc, "lunch": lc, "dinner": dc, "supper": sc,
            "total": bc + lc + dc + sc,
        },
    }


@router.get("/monthly-sales")
async def monthly_sales(
    start_month: str = Query(..., description="YYYY-MM"),
    end_month: str = Query(..., description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly sales trend."""
    result = await db.execute(
        select(
            CustomerSettlement.settlement_month,
            func.sum(CustomerSettlement.final_amount),
        )
        .where(
            CustomerSettlement.settlement_month >= start_month,
            CustomerSettlement.settlement_month <= end_month,
        )
        .group_by(CustomerSettlement.settlement_month)
        .order_by(CustomerSettlement.settlement_month)
    )
    rows = result.all()
    return [{"month": r[0], "amount": float(r[1])} for r in rows]


@router.get("/category-usage")
async def category_usage(
    month: str = Query(..., description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Goods category usage ratio for a month."""
    year, mon = int(month[:4]), int(month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    result = await db.execute(
        select(
            ProductCategory.name,
            func.sum(InventoryTransactionItem.amount),
        )
        .join(Product, InventoryTransactionItem.product_id == Product.id)
        .join(ProductCategory, Product.category_id == ProductCategory.id)
        .join(InventoryTransaction, InventoryTransactionItem.transaction_id == InventoryTransaction.id)
        .where(
            InventoryTransaction.transaction_type.in_(["outbound", "inbound"]),
            InventoryTransaction.transaction_date >= start,
            InventoryTransaction.transaction_date < end,
        )
        .group_by(ProductCategory.name)
        .order_by(func.sum(InventoryTransactionItem.amount).desc())
    )
    rows = result.all()
    return [{"category": r[0], "amount": float(r[1])} for r in rows]


@router.get("/customer-revenue")
async def customer_revenue(
    month: str = Query(..., description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revenue breakdown by customer."""
    from app.models.customer import Customer
    result = await db.execute(
        select(
            Customer.name,
            CustomerSettlement.final_amount,
        )
        .join(Customer, CustomerSettlement.customer_id == Customer.id)
        .where(CustomerSettlement.settlement_month == month)
        .order_by(CustomerSettlement.final_amount.desc())
    )
    return [{"customer": r[0], "amount": float(r[1])} for r in result.all()]
