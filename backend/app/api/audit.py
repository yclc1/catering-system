"""Audit Log and Monthly Close API."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.models.audit import AuditLog
from app.models.monthly_close import MonthlyClose
from app.schemas.audit import AuditLogResponse
from app.schemas import PageResponse, MessageResponse
from app.services.monthly_close_service import close_month, reopen_month

audit_router = APIRouter(prefix="/audit-logs", tags=["审计日志"])
monthly_close_router = APIRouter(prefix="/monthly-closes", tags=["月结管理"])


@audit_router.get("", response_model=PageResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size))
    logs = result.scalars().all()

    items = [AuditLogResponse(
        id=l.id, user_id=l.user_id, username=l.username, action=l.action,
        resource_type=l.resource_type, resource_id=l.resource_id,
        resource_code=l.resource_code, detail=l.detail,
        ip_address=l.ip_address, created_at=str(l.created_at),
    ) for l in logs]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


# --- Monthly Close ---

@monthly_close_router.get("")
async def list_monthly_closes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(MonthlyClose).order_by(MonthlyClose.close_month.desc()))
    closes = result.scalars().all()
    return [{
        "id": mc.id, "close_month": mc.close_month, "status": mc.status,
        "closed_at": str(mc.closed_at) if mc.closed_at else None,
        "reopened_at": str(mc.reopened_at) if mc.reopened_at else None,
        "notes": mc.notes,
    } for mc in closes]


from pydantic import BaseModel

class CloseMonthRequest(BaseModel):
    month: str  # YYYY-MM

class ReopenMonthRequest(BaseModel):
    reason: str


@monthly_close_router.post("", response_model=MessageResponse)
async def close_month_api(
    data: CloseMonthRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("monthly_close:create")),
):
    await close_month(db, data.month, current_user.id, current_user.username)
    return MessageResponse(message=f"月份 {data.month} 已关闭")


@monthly_close_router.post("/{close_id}/reopen", response_model=MessageResponse)
async def reopen_month_api(
    close_id: int, data: ReopenMonthRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("monthly_close:reopen")),
):
    result = await db.execute(select(MonthlyClose).where(MonthlyClose.id == close_id))
    mc = result.scalar_one_or_none()
    if not mc:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("月结记录", close_id)
    await reopen_month(db, mc.close_month, current_user.id, current_user.username, data.reason)
    return MessageResponse(message=f"月份 {mc.close_month} 已重新打开")
