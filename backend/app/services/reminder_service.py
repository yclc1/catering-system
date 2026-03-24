"""Reminder service: check for upcoming expirations and queue notifications."""
from datetime import date, timedelta, datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.vehicle import Vehicle
from app.models.notification import NotificationQueue
from app.models.user import User


async def check_contract_reminders(db: AsyncSession):
    """Queue notifications for contracts expiring soon."""
    today = date.today()
    threshold = today + timedelta(days=60)

    result = await db.execute(
        select(Contract).where(
            Contract.is_deleted == False,
            Contract.status == "active",
            Contract.end_date <= threshold,
            Contract.end_date >= today,
        )
    )
    contracts = result.scalars().all()

    for c in contracts:
        days_left = (c.end_date - today).days
        # Queue notification for admin users
        admins = await db.execute(
            select(User).where(User.is_active == True, User.wechat_openid.isnot(None))
        )
        for user in admins.scalars().all():
            existing = await db.execute(
                select(NotificationQueue).where(
                    NotificationQueue.recipient_user_id == user.id,
                    NotificationQueue.title == f"合同到期提醒: {c.title}",
                    NotificationQueue.status.in_(["pending", "sent"]),
                )
            )
            if not existing.scalar_one_or_none():
                notif = NotificationQueue(
                    recipient_user_id=user.id,
                    recipient_openid=user.wechat_openid,
                    channel="wechat",
                    title=f"合同到期提醒: {c.title}",
                    content=f"合同 [{c.code}] {c.title} 将于 {c.end_date} 到期 (还剩{days_left}天)",
                )
                db.add(notif)

    await db.commit()


async def check_vehicle_reminders(db: AsyncSession):
    """Queue notifications for vehicle insurance/maintenance due."""
    today = date.today()
    threshold = today + timedelta(days=30)

    result = await db.execute(
        select(Vehicle).where(
            Vehicle.is_deleted == False,
            (Vehicle.insurance_expiry_date <= threshold) | (Vehicle.next_maintenance_date <= threshold),
        )
    )
    vehicles = result.scalars().all()

    admins = await db.execute(
        select(User).where(User.is_active == True, User.wechat_openid.isnot(None))
    )
    admin_users = admins.scalars().all()

    for v in vehicles:
        messages = []
        if v.insurance_expiry_date and v.insurance_expiry_date <= threshold:
            days = (v.insurance_expiry_date - today).days
            messages.append(f"车辆 {v.plate_number} 保险将于 {v.insurance_expiry_date} 到期 (还剩{days}天)")
        if v.next_maintenance_date and v.next_maintenance_date <= threshold:
            days = (v.next_maintenance_date - today).days
            messages.append(f"车辆 {v.plate_number} 需于 {v.next_maintenance_date} 前保养 (还剩{days}天)")

        for msg in messages:
            for user in admin_users:
                existing = await db.execute(
                    select(NotificationQueue).where(
                        NotificationQueue.recipient_user_id == user.id,
                        NotificationQueue.content == msg,
                        NotificationQueue.status.in_(["pending", "sent"]),
                    )
                )
                if not existing.scalar_one_or_none():
                    notif = NotificationQueue(
                        recipient_user_id=user.id,
                        recipient_openid=user.wechat_openid,
                        channel="wechat",
                        title="车辆提醒",
                        content=msg,
                    )
                    db.add(notif)

    await db.commit()
