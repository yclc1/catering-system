"""Audit log service."""
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[int],
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    resource_code: Optional[str] = None,
    detail: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_code=resource_code,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.flush()
    return log
