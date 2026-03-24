"""Supplier Reconciliation API."""
from typing import Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.reconciliation import SupplierReconciliation
from app.models.inventory import InventoryTransaction
from app.models.account import PaymentRecord
from app.core.exceptions import NotFoundError
from app.schemas.reconciliation import ReconciliationGenerateRequest, ReconciliationUpdateRequest, SupplierReconciliationResponse
from app.schemas import PageResponse, MessageResponse
from app.schemas.inventory import InventoryTransactionResponse, InventoryTransactionItemResponse
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/reconciliations/suppliers", tags=["供应商对账"])


@router.get("", response_model=PageResponse[SupplierReconciliationResponse])
async def list_reconciliations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SupplierReconciliation)
    count_query = select(func.count(SupplierReconciliation.id))

    if supplier_id:
        query = query.where(SupplierReconciliation.supplier_id == supplier_id)
        count_query = count_query.where(SupplierReconciliation.supplier_id == supplier_id)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(SupplierReconciliation.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [SupplierReconciliationResponse(
        id=r.id, supplier_id=r.supplier_id,
        supplier_name=r.supplier.name if r.supplier else None,
        reconciliation_month=r.reconciliation_month,
        total_inbound_amount=r.total_inbound_amount,
        total_return_amount=r.total_return_amount,
        net_amount=r.net_amount,
        paid_amount=r.paid_amount,
        outstanding_amount=r.outstanding_amount,
        status=r.status, notes=r.notes,
    ) for r in result.scalars().all()]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("/generate", response_model=SupplierReconciliationResponse)
async def generate_reconciliation(
    data: ReconciliationGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    year, mon = int(data.month[:4]), int(data.month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    # Calculate inbound total
    inbound_result = await db.execute(
        select(func.coalesce(func.sum(InventoryTransaction.total_amount), 0))
        .where(
            InventoryTransaction.supplier_id == data.supplier_id,
            InventoryTransaction.transaction_type == "inbound",
            InventoryTransaction.status == "confirmed",
            InventoryTransaction.transaction_date >= start,
            InventoryTransaction.transaction_date < end,
        )
    )
    total_inbound = inbound_result.scalar()

    # Calculate return total
    return_result = await db.execute(
        select(func.coalesce(func.sum(InventoryTransaction.total_amount), 0))
        .where(
            InventoryTransaction.supplier_id == data.supplier_id,
            InventoryTransaction.transaction_type == "return_supplier",
            InventoryTransaction.status == "confirmed",
            InventoryTransaction.transaction_date >= start,
            InventoryTransaction.transaction_date < end,
        )
    )
    total_return = return_result.scalar()

    # Calculate paid amount
    paid_result = await db.execute(
        select(func.coalesce(func.sum(PaymentRecord.amount), 0))
        .where(
            PaymentRecord.supplier_id == data.supplier_id,
            PaymentRecord.direction == "outbound",
            PaymentRecord.payment_date >= start,
            PaymentRecord.payment_date < end,
        )
    )
    paid_amount = paid_result.scalar()

    net_amount = total_inbound - total_return
    outstanding = net_amount - paid_amount

    # Upsert
    existing = await db.execute(
        select(SupplierReconciliation).where(
            SupplierReconciliation.supplier_id == data.supplier_id,
            SupplierReconciliation.reconciliation_month == data.month,
        )
    )
    recon = existing.scalar_one_or_none()
    if recon:
        recon.total_inbound_amount = total_inbound
        recon.total_return_amount = total_return
        recon.net_amount = net_amount
        recon.paid_amount = paid_amount
        recon.outstanding_amount = outstanding
        recon.updated_by = current_user.id
    else:
        recon = SupplierReconciliation(
            supplier_id=data.supplier_id,
            reconciliation_month=data.month,
            total_inbound_amount=total_inbound,
            total_return_amount=total_return,
            net_amount=net_amount,
            paid_amount=paid_amount,
            outstanding_amount=outstanding,
            created_by=current_user.id,
        )
        db.add(recon)

    await db.flush()
    return SupplierReconciliationResponse(
        id=recon.id, supplier_id=recon.supplier_id,
        supplier_name=recon.supplier.name if recon.supplier else None,
        reconciliation_month=recon.reconciliation_month,
        total_inbound_amount=recon.total_inbound_amount,
        total_return_amount=recon.total_return_amount,
        net_amount=recon.net_amount, paid_amount=recon.paid_amount,
        outstanding_amount=recon.outstanding_amount,
        status=recon.status, notes=recon.notes,
    )


@router.get("/{recon_id}", response_model=SupplierReconciliationResponse)
async def get_reconciliation(recon_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SupplierReconciliation).where(SupplierReconciliation.id == recon_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("对账记录", recon_id)
    return SupplierReconciliationResponse(
        id=r.id, supplier_id=r.supplier_id,
        supplier_name=r.supplier.name if r.supplier else None,
        reconciliation_month=r.reconciliation_month,
        total_inbound_amount=r.total_inbound_amount,
        total_return_amount=r.total_return_amount,
        net_amount=r.net_amount, paid_amount=r.paid_amount,
        outstanding_amount=r.outstanding_amount,
        status=r.status, notes=r.notes,
    )


@router.get("/{recon_id}/transactions", response_model=list[InventoryTransactionResponse])
async def get_reconciliation_transactions(recon_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Drill down to all inbound/return transactions for this reconciliation."""
    result = await db.execute(select(SupplierReconciliation).where(SupplierReconciliation.id == recon_id))
    recon = result.scalar_one_or_none()
    if not recon:
        raise NotFoundError("对账记录", recon_id)

    year, mon = int(recon.reconciliation_month[:4]), int(recon.reconciliation_month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    txn_result = await db.execute(
        select(InventoryTransaction)
        .where(
            InventoryTransaction.supplier_id == recon.supplier_id,
            InventoryTransaction.transaction_type.in_(["inbound", "return_supplier"]),
            InventoryTransaction.status == "confirmed",
            InventoryTransaction.transaction_date >= start,
            InventoryTransaction.transaction_date < end,
        )
        .order_by(InventoryTransaction.transaction_date)
    )
    txns = txn_result.scalars().all()

    return [InventoryTransactionResponse(
        id=t.id, code=t.code, transaction_type=t.transaction_type,
        transaction_date=t.transaction_date,
        supplier_id=t.supplier_id, supplier_name=t.supplier.name if t.supplier else None,
        customer_id=t.customer_id, customer_name=None,
        status=t.status, total_amount=t.total_amount,
        items=[InventoryTransactionItemResponse(
            id=i.id, product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            product_code=i.product.code if i.product else None,
            product_unit=i.product.unit if i.product else None,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, batch_no=i.batch_no,
        ) for i in t.items],
        notes=t.notes, month_closed=t.month_closed,
    ) for t in txns]


@router.post("/{recon_id}/confirm", response_model=MessageResponse)
async def confirm_reconciliation(recon_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SupplierReconciliation).where(SupplierReconciliation.id == recon_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("对账记录", recon_id)
    r.status = "confirmed"
    r.updated_by = current_user.id
    await create_audit_log(db, current_user.id, current_user.username, "confirm", "supplier_reconciliation", resource_id=r.id)
    return MessageResponse(message="对账已确认")


@router.get("/{recon_id}/export")
async def export_reconciliation(recon_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SupplierReconciliation).where(SupplierReconciliation.id == recon_id))
    recon = result.scalar_one_or_none()
    if not recon:
        raise NotFoundError("对账记录", recon_id)

    year, mon = int(recon.reconciliation_month[:4]), int(recon.reconciliation_month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    txn_result = await db.execute(
        select(InventoryTransaction)
        .where(
            InventoryTransaction.supplier_id == recon.supplier_id,
            InventoryTransaction.transaction_type.in_(["inbound", "return_supplier"]),
            InventoryTransaction.transaction_date >= start,
            InventoryTransaction.transaction_date < end,
        )
        .order_by(InventoryTransaction.transaction_date)
    )
    txns = txn_result.scalars().all()

    from app.services.excel_service import export_supplier_reconciliation
    supplier_name = recon.supplier.name if recon.supplier else "未知供应商"
    output = export_supplier_reconciliation(supplier_name, recon, txns)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=recon_{supplier_name}_{recon.reconciliation_month}.xlsx"},
    )
