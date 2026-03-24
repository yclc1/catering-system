"""Supplier API."""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.supplier import Supplier
from app.core.exceptions import NotFoundError
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.services import generate_code
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/suppliers", tags=["供应商管理"])


@router.get("", response_model=PageResponse[SupplierResponse])
async def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Supplier).where(Supplier.is_deleted == False)
    count_query = select(func.count(Supplier.id)).where(Supplier.is_deleted == False)

    if keyword:
        query = query.where(Supplier.name.ilike(f"%{keyword}%") | Supplier.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(Supplier.name.ilike(f"%{keyword}%") | Supplier.code.ilike(f"%{keyword}%"))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Supplier.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [SupplierResponse.model_validate(s) for s in result.scalars().all()]

    return PageResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=SupplierResponse)
async def create_supplier(
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    code = await generate_code(db, "supplier")
    supplier = Supplier(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(supplier)
    await db.flush()
    await create_audit_log(db, current_user.id, current_user.username, "create", "supplier", resource_id=supplier.id, resource_code=code)
    return SupplierResponse.model_validate(supplier)


@router.get("/dropdown", response_model=list[DropdownItem])
async def supplier_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Supplier).where(Supplier.is_deleted == False).order_by(Supplier.name)
    )
    return [DropdownItem(id=s.id, name=s.name, code=s.code) for s in result.scalars().all()]


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id, Supplier.is_deleted == False))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("供应商", supplier_id)
    return SupplierResponse.model_validate(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int, data: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id, Supplier.is_deleted == False))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("供应商", supplier_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    supplier.updated_by = current_user.id

    await create_audit_log(db, current_user.id, current_user.username, "update", "supplier", resource_id=supplier.id, resource_code=supplier.code)
    await db.flush()
    return SupplierResponse.model_validate(supplier)


@router.delete("/{supplier_id}", response_model=MessageResponse)
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id, Supplier.is_deleted == False))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("供应商", supplier_id)

    supplier.is_deleted = True
    supplier.deleted_at = datetime.now(timezone.utc)
    await create_audit_log(db, current_user.id, current_user.username, "delete", "supplier", resource_id=supplier.id, resource_code=supplier.code)
    return MessageResponse(message="供应商已删除")
