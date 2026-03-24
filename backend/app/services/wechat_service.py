"""WeChat notification service."""
import httpx
import asyncio
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.notification import NotificationQueue


_access_token: Optional[str] = None
_token_expires_at: Optional[datetime] = None
_token_lock = asyncio.Lock()


async def get_wechat_access_token() -> Optional[str]:
    global _access_token, _token_expires_at

    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        return None

    now = datetime.now(timezone.utc)
    if _access_token and _token_expires_at and now < _token_expires_at:
        return _access_token

    async with _token_lock:
        # Double check after acquiring lock
        if _access_token and _token_expires_at and now < _token_expires_at:
            return _access_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                },
            )
            data = resp.json()
            if "access_token" in data:
                _access_token = data["access_token"]
                from datetime import timedelta
                _token_expires_at = now + timedelta(seconds=data.get("expires_in", 7200) - 300)
                return _access_token
    return None


async def send_wechat_template_message(openid: str, template_id: str, data: dict, url: str = "") -> bool:
    token = await get_wechat_access_token()
    if not token:
        return False

    payload = {
        "touser": openid,
        "template_id": template_id,
        "url": url,
        "data": data,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}",
            json=payload,
        )
        result = resp.json()
        return result.get("errcode") == 0


async def process_notification_queue(db: AsyncSession):
    """Process pending notifications in the queue."""
    result = await db.execute(
        select(NotificationQueue)
        .where(NotificationQueue.status == "pending", NotificationQueue.retry_count < 3)
        .order_by(NotificationQueue.id)
        .limit(50)
        .with_for_update(skip_locked=True)
    )
    notifications = result.scalars().all()

    for notif in notifications:
        notif.status = "sending"
        await db.flush()

        success = False
        if notif.channel == "wechat" and notif.recipient_openid:
            success = await send_wechat_template_message(
                openid=notif.recipient_openid,
                template_id=settings.WECHAT_TEMPLATE_ID or "",
                data={
                    "first": {"value": notif.title},
                    "keyword1": {"value": notif.content},
                    "remark": {"value": "团膳管理系统"},
                },
            )

        if success:
            notif.status = "sent"
            notif.sent_at = datetime.now(timezone.utc)
        else:
            notif.retry_count += 1
            notif.status = "failed" if notif.retry_count >= 3 else "pending"

        await db.flush()
    await db.commit()
