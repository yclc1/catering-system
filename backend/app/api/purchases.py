"""Purchase Order API."""
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.inventory import InventoryTransaction, InventoryTransactionItem, InventoryStock
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.purchase import PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, PurchaseOrderItemResponse
from app.schemas import PageResponse, MessageResponse
from app.services import generate_code
from app.services.audit_service import create_audit_log
from app.services.monthly_close_service import check_month_not_closed

router = APIRouter(prefix="/purchases", tags=["采购管理"])


@router.get("", response_model=PageResponse[PurchaseOrderResponse])
async def list_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PurchaseOrder)
    count_query = select(func.count(PurchaseOrder.id))

    if keyword:
        query = query.where(PurchaseOrder.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(PurchaseOrder.code.ilike(f"%{keyword}%"))
    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
        count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(PurchaseOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))
    orders = result.scalars().all()

    items = []
    for po in orders:
        items.append(PurchaseOrderResponse(
            id=po.id, code=po.code, supplier_id=po.supplier_id,
            supplier_name=po.supplier.name if po.supplier else None,
            order_date=po.order_date, status=po.status, total_amount=po.total_amount,
            items=[PurchaseOrderItemResponse(
                id=i.id, product_id=i.product_id,
                product_name=i.product.name if i.product else None,
                product_code=i.product.code if i.product else None,
                product_unit=i.product.unit if i.product else None,
                quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, notes=i.notes,
            ) for i in po.items],
            notes=po.notes, month_closed=po.month_closed,
        ))

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("", response_model=PurchaseOrderResponse)
async def create_purchase(data: PurchaseOrderCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await check_month_not_closed(db, data.order_date)

    code = await generate_code(db, "purchase_order")
    total = Decimal("0")
    po = PurchaseOrder(
        code=code, supplier_id=data.supplier_id, order_date=data.order_date,
        notes=data.notes, created_by=current_user.id,
    )
    db.add(po)
    await db.flush()

    for item_data in data.items:
        amount = item_data.quantity * item_data.unit_price
        total += amount
        poi = PurchaseOrderItem(
            purchase_order_id=po.id, product_id=item_data.product_id,
            quantity=item_data.quantity, unit_price=item_data.unit_price,
            amount=amount, notes=item_data.notes,
        )
        db.add(poi)

    po.total_amount = total
    await db.flush()

    # Reload
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po.id))
    po = result.scalar_one()
    await create_audit_log(db, current_user.id, current_user.username, "create", "purchase_order", resource_id=po.id, resource_code=code)

    return PurchaseOrderResponse(
        id=po.id, code=po.code, supplier_id=po.supplier_id,
        supplier_name=po.supplier.name if po.supplier else None,
        order_date=po.order_date, status=po.status, total_amount=po.total_amount,
        items=[PurchaseOrderItemResponse(
            id=i.id, product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            product_code=i.product.code if i.product else None,
            product_unit=i.product.unit if i.product else None,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, notes=i.notes,
        ) for i in po.items],
        notes=po.notes, month_closed=po.month_closed,
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase(po_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单", po_id)
    return PurchaseOrderResponse(
        id=po.id, code=po.code, supplier_id=po.supplier_id,
        supplier_name=po.supplier.name if po.supplier else None,
        order_date=po.order_date, status=po.status, total_amount=po.total_amount,
        items=[PurchaseOrderItemResponse(
            id=i.id, product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            product_code=i.product.code if i.product else None,
            product_unit=i.product.unit if i.product else None,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, notes=i.notes,
        ) for i in po.items],
        notes=po.notes, month_closed=po.month_closed,
    )


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase(po_id: int, data: PurchaseOrderUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单", po_id)
    if po.status != "draft":
        raise BusinessError("只能修改草稿状态的采购单")
    if po.month_closed:
        raise BusinessError("该月份已锁定")

    if data.supplier_id is not None:
        po.supplier_id = data.supplier_id
    if data.order_date is not None:
        po.order_date = data.order_date
    if data.notes is not None:
        po.notes = data.notes

    if data.items is not None:
        # Remove old items
        for old_item in po.items:
            await db.delete(old_item)
        await db.flush()

        total = Decimal("0")
        for item_data in data.items:
            amount = item_data.quantity * item_data.unit_price
            total += amount
            poi = PurchaseOrderItem(
                purchase_order_id=po.id, product_id=item_data.product_id,
                quantity=item_data.quantity, unit_price=item_data.unit_price,
                amount=amount, notes=item_data.notes,
            )
            db.add(poi)
        po.total_amount = total

    po.updated_by = current_user.id
    await db.flush()

    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po.id))
    po = result.scalar_one()
    return PurchaseOrderResponse(
        id=po.id, code=po.code, supplier_id=po.supplier_id,
        supplier_name=po.supplier.name if po.supplier else None,
        order_date=po.order_date, status=po.status, total_amount=po.total_amount,
        items=[PurchaseOrderItemResponse(
            id=i.id, product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            product_code=i.product.code if i.product else None,
            product_unit=i.product.unit if i.product else None,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, notes=i.notes,
        ) for i in po.items],
        notes=po.notes, month_closed=po.month_closed,
    )


@router.delete("/{po_id}", response_model=MessageResponse)
async def cancel_purchase(po_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单", po_id)
    if po.status != "draft":
        raise BusinessError("只能取消草稿状态的采购单")
    po.status = "cancelled"
    return MessageResponse(message="采购单已取消")


@router.post("/{po_id}/confirm", response_model=MessageResponse)
async def confirm_purchase(po_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Confirm PO and auto-create inventory inbound transaction."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单", po_id)
    if po.status != "draft":
        raise BusinessError("只能确认草稿状态的采购单")

    po.status = "confirmed"

    # Create inventory inbound
    it_code = await generate_code(db, "inventory_transaction")
    it = InventoryTransaction(
        code=it_code, transaction_type="inbound", transaction_date=po.order_date,
        reference_type="purchase_order", reference_id=po.id,
        supplier_id=po.supplier_id, total_amount=po.total_amount,
        created_by=current_user.id,
    )
    db.add(it)
    await db.flush()

    for poi in po.items:
        iti = InventoryTransactionItem(
            transaction_id=it.id, product_id=poi.product_id,
            quantity=poi.quantity, unit_price=poi.unit_price, amount=poi.amount,
        )
        db.add(iti)

        # Update inventory stock
        stock_result = await db.execute(
            select(InventoryStock).where(InventoryStock.product_id == poi.product_id).with_for_update()
        )
        stock = stock_result.scalar_one_or_none()
        if stock is None:
            stock = InventoryStock(product_id=poi.product_id, current_qty=poi.quantity, avg_unit_cost=poi.unit_price)
            db.add(stock)
        else:
            # Weighted average cost
            total_value = stock.current_qty * stock.avg_unit_cost + poi.quantity * poi.unit_price
            stock.current_qty += poi.quantity
            if stock.current_qty > 0:
                stock.avg_unit_cost = (total_value / stock.current_qty).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        stock.last_inbound_date = po.order_date

    await create_audit_log(db, current_user.id, current_user.username, "confirm", "purchase_order", resource_id=po.id, resource_code=po.code)
    await db.flush()
    return MessageResponse(message="采购单已确认，库存已入库")
