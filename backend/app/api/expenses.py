"""Expense Approval API."""
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.expense import ExpenseApproval, ExpenseItem, ExpenseCategory
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.expense import (
    ExpenseApprovalCreate, ExpenseApprovalUpdate, ExpenseApprovalResponse,
    ExpenseItemResponse, ExpenseCategoryCreate, ExpenseCategoryResponse, RejectRequest,
)
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.services import generate_code
from app.services.audit_service import create_audit_log
from app.services.monthly_close_service import check_month_not_closed

router = APIRouter(prefix="/expenses", tags=["费用审批"])
category_router = APIRouter(prefix="/expense-categories", tags=["费用类别"])


@router.get("", response_model=PageResponse[ExpenseApprovalResponse])
async def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ExpenseApproval)
    count_query = select(func.count(ExpenseApproval.id))

    if status:
        query = query.where(ExpenseApproval.status == status)
        count_query = count_query.where(ExpenseApproval.status == status)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(ExpenseApproval.id.desc()).offset((page - 1) * page_size).limit(page_size))
    expenses = result.scalars().all()

    items = [ExpenseApprovalResponse(
        id=e.id, code=e.code, applicant_id=e.applicant_id,
        applicant_name=e.applicant.real_name if e.applicant else None,
        approver_id=e.approver_id,
        approver_name=e.approver.real_name if e.approver else None,
        category_id=e.category_id,
        category_name=e.category.name if e.category else None,
        title=e.title, total_amount=e.total_amount, expense_date=e.expense_date,
        status=e.status, approved_at=str(e.approved_at) if e.approved_at else None,
        reject_reason=e.reject_reason,
        items=[ExpenseItemResponse(id=i.id, description=i.description, amount=i.amount, attachment_url=i.attachment_url) for i in e.items],
        notes=e.notes, month_closed=e.month_closed,
    ) for e in expenses]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("", response_model=ExpenseApprovalResponse)
async def create_expense(data: ExpenseApprovalCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await check_month_not_closed(db, data.expense_date)

    code = await generate_code(db, "expense")
    expense = ExpenseApproval(
        code=code, applicant_id=current_user.id, approver_id=data.approver_id,
        category_id=data.category_id, title=data.title, total_amount=data.total_amount,
        expense_date=data.expense_date, notes=data.notes, created_by=current_user.id,
    )
    db.add(expense)
    await db.flush()

    for item_data in data.items:
        item = ExpenseItem(expense_approval_id=expense.id, **item_data.model_dump())
        db.add(item)
    await db.flush()

    result = await db.execute(select(ExpenseApproval).where(ExpenseApproval.id == expense.id))
    e = result.scalar_one()
    await create_audit_log(db, current_user.id, current_user.username, "create", "expense", resource_id=e.id, resource_code=code)

    return ExpenseApprovalResponse(
        id=e.id, code=e.code, applicant_id=e.applicant_id,
        applicant_name=e.applicant.real_name if e.applicant else None,
        approver_id=e.approver_id,
        approver_name=e.approver.real_name if e.approver else None,
        category_id=e.category_id,
        category_name=e.category.name if e.category else None,
        title=e.title, total_amount=e.total_amount, expense_date=e.expense_date,
        status=e.status, items=[ExpenseItemResponse(id=i.id, description=i.description, amount=i.amount, attachment_url=i.attachment_url) for i in e.items],
        notes=e.notes, month_closed=e.month_closed,
    )


@router.post("/{expense_id}/approve", response_model=MessageResponse)
async def approve_expense(expense_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ExpenseApproval).where(ExpenseApproval.id == expense_id))
    e = result.scalar_one_or_none()
    if not e:
        raise NotFoundError("费用审批", expense_id)
    if e.status != "pending":
        raise BusinessError("只能审批待审核状态的费用")
    e.status = "approved"
    e.approved_at = datetime.now(timezone.utc)
    e.updated_by = current_user.id
    await create_audit_log(db, current_user.id, current_user.username, "approve", "expense", resource_id=e.id, resource_code=e.code)
    return MessageResponse(message="费用已审批通过")


@router.post("/{expense_id}/reject", response_model=MessageResponse)
async def reject_expense(expense_id: int, data: RejectRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ExpenseApproval).where(ExpenseApproval.id == expense_id))
    e = result.scalar_one_or_none()
    if not e:
        raise NotFoundError("费用审批", expense_id)
    if e.status != "pending":
        raise BusinessError("只能驳回待审核状态的费用")
    e.status = "rejected"
    e.reject_reason = data.reason
    e.updated_by = current_user.id
    await create_audit_log(db, current_user.id, current_user.username, "reject", "expense", resource_id=e.id, resource_code=e.code)
    return MessageResponse(message="费用已驳回")


@router.get("/{expense_id}", response_model=ExpenseApprovalResponse)
async def get_expense(expense_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ExpenseApproval).where(ExpenseApproval.id == expense_id))
    e = result.scalar_one_or_none()
    if not e:
        raise NotFoundError("费用审批", expense_id)
    return ExpenseApprovalResponse(
        id=e.id, code=e.code, applicant_id=e.applicant_id,
        applicant_name=e.applicant.real_name if e.applicant else None,
        approver_id=e.approver_id,
        approver_name=e.approver.real_name if e.approver else None,
        category_id=e.category_id,
        category_name=e.category.name if e.category else None,
        title=e.title, total_amount=e.total_amount, expense_date=e.expense_date,
        status=e.status, approved_at=str(e.approved_at) if e.approved_at else None,
        reject_reason=e.reject_reason,
        items=[ExpenseItemResponse(id=i.id, description=i.description, amount=i.amount, attachment_url=i.attachment_url) for i in e.items],
        notes=e.notes, month_closed=e.month_closed,
    )


# --- Expense Categories ---

@category_router.get("", response_model=list[ExpenseCategoryResponse])
async def list_expense_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ExpenseCategory).where(ExpenseCategory.is_deleted == False).order_by(ExpenseCategory.sort_order))
    return [ExpenseCategoryResponse.model_validate(c) for c in result.scalars().all()]


@category_router.post("", response_model=ExpenseCategoryResponse)
async def create_expense_category(data: ExpenseCategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cat = ExpenseCategory(**data.model_dump(), created_by=current_user.id)
    db.add(cat)
    await db.flush()
    return ExpenseCategoryResponse.model_validate(cat)


@category_router.get("/dropdown", response_model=list[DropdownItem])
async def expense_category_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ExpenseCategory).where(ExpenseCategory.is_deleted == False).order_by(ExpenseCategory.sort_order))
    return [DropdownItem(id=c.id, name=c.name) for c in result.scalars().all()]
