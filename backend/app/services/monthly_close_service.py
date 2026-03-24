"""Monthly close service."""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monthly_close import MonthlyClose
from app.models.purchase import PurchaseOrder
from app.models.inventory import InventoryTransaction
from app.models.customer import MealRegistration
from app.models.account import PaymentRecord
from app.models.expense import ExpenseApproval
from app.core.exceptions import BusinessError, MonthClosedError
from app.services.audit_service import create_audit_log


async def is_month_closed(db: AsyncSession, month: str) -> bool:
    """Check if a month is closed."""
    result = await db.execute(
        select(MonthlyClose).where(
            MonthlyClose.close_month == month,
            MonthlyClose.status == "closed",
        )
    )
    return result.scalar_one_or_none() is not None


async def check_month_not_closed(db: AsyncSession, date_value) -> None:
    """Raise error if the month containing the date is closed."""
    if date_value is None:
        return
    if hasattr(date_value, "strftime"):
        month = date_value.strftime("%Y-%m")
    else:
        month = str(date_value)[:7]
    if await is_month_closed(db, month):
        raise MonthClosedError(month)


async def close_month(db: AsyncSession, month: str, user_id: int, username: str):
    """Close a month - lock all financial records."""
    if await is_month_closed(db, month):
        raise BusinessError(f"月份 {month} 已经关闭")

    # Parse month boundaries
    year, mon = int(month[:4]), int(month[5:7])
    from datetime import date
    start_date = date(year, mon, 1)
    if mon == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, mon + 1, 1)

    # Lock purchase orders
    await db.execute(
        update(PurchaseOrder)
        .where(PurchaseOrder.order_date >= start_date, PurchaseOrder.order_date < end_date)
        .values(month_closed=True)
    )

    # Lock inventory transactions
    await db.execute(
        update(InventoryTransaction)
        .where(InventoryTransaction.transaction_date >= start_date, InventoryTransaction.transaction_date < end_date)
        .values(month_closed=True)
    )

    # Lock meal registrations
    await db.execute(
        update(MealRegistration)
        .where(MealRegistration.meal_date >= start_date, MealRegistration.meal_date < end_date)
        .values(month_closed=True)
    )

    # Lock payment records
    await db.execute(
        update(PaymentRecord)
        .where(PaymentRecord.payment_date >= start_date, PaymentRecord.payment_date < end_date)
        .values(month_closed=True)
    )

    # Lock expense approvals
    await db.execute(
        update(ExpenseApproval)
        .where(ExpenseApproval.expense_date >= start_date, ExpenseApproval.expense_date < end_date)
        .values(month_closed=True)
    )

    # Create or update monthly close record
    result = await db.execute(
        select(MonthlyClose).where(MonthlyClose.close_month == month)
    )
    mc = result.scalar_one_or_none()
    if mc is None:
        mc = MonthlyClose(close_month=month)
        db.add(mc)

    mc.status = "closed"
    mc.closed_by = user_id
    mc.closed_at = datetime.now(timezone.utc)

    await create_audit_log(
        db, user_id, username, "close_month", "monthly_close",
        resource_code=month,
        detail={"month": month, "action": "close"},
    )
    await db.flush()
    return mc


async def reopen_month(db: AsyncSession, month: str, user_id: int, username: str, reason: str):
    """Reopen a closed month (admin only)."""
    result = await db.execute(
        select(MonthlyClose).where(
            MonthlyClose.close_month == month,
            MonthlyClose.status == "closed",
        )
    )
    mc = result.scalar_one_or_none()
    if mc is None:
        raise BusinessError(f"月份 {month} 未关闭，无法重新打开")

    mc.status = "reopened"
    mc.reopened_by = user_id
    mc.reopened_at = datetime.now(timezone.utc)
    mc.notes = reason

    # Unlock records (set month_closed = False)
    year, mon = int(month[:4]), int(month[5:7])
    from datetime import date
    start_date = date(year, mon, 1)
    if mon == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, mon + 1, 1)

    for model_cls, date_col in [
        (PurchaseOrder, PurchaseOrder.order_date),
        (InventoryTransaction, InventoryTransaction.transaction_date),
        (MealRegistration, MealRegistration.meal_date),
        (PaymentRecord, PaymentRecord.payment_date),
        (ExpenseApproval, ExpenseApproval.expense_date),
    ]:
        await db.execute(
            update(model_cls)
            .where(date_col >= start_date, date_col < end_date)
            .values(month_closed=False)
        )

    await create_audit_log(
        db, user_id, username, "reopen_month", "monthly_close",
        resource_code=month,
        detail={"month": month, "action": "reopen", "reason": reason},
    )
    await db.flush()
    return mc
