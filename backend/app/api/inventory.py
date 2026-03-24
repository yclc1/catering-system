"""Inventory API."""
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.inventory import InventoryTransaction, InventoryTransactionItem, InventoryStock
from app.core.exceptions import NotFoundError, BusinessError
from app.schemas.inventory import (
    InventoryTransactionCreate, InventoryTransactionResponse, InventoryTransactionItemResponse,
    InventoryStockResponse,
)
from app.schemas import PageResponse, MessageResponse
from app.services import generate_code
from app.services.audit_service import create_audit_log
from app.services.monthly_close_service import check_month_not_closed

router = APIRouter(prefix="/inventory", tags=["库存管理"])


@router.get("/transactions", response_model=PageResponse[InventoryTransactionResponse])
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(InventoryTransaction)
    count_query = select(func.count(InventoryTransaction.id))

    if transaction_type:
        query = query.where(InventoryTransaction.transaction_type == transaction_type)
        count_query = count_query.where(InventoryTransaction.transaction_type == transaction_type)
    if keyword:
        query = query.where(InventoryTransaction.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(InventoryTransaction.code.ilike(f"%{keyword}%"))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(InventoryTransaction.id.desc()).offset((page - 1) * page_size).limit(page_size))
    txns = result.scalars().all()

    items = []
    for t in txns:
        items.append(InventoryTransactionResponse(
            id=t.id, code=t.code, transaction_type=t.transaction_type,
            transaction_date=t.transaction_date,
            supplier_id=t.supplier_id, supplier_name=t.supplier.name if t.supplier else None,
            customer_id=t.customer_id, customer_name=t.customer.name if t.customer else None,
            status=t.status, total_amount=t.total_amount,
            items=[InventoryTransactionItemResponse(
                id=i.id, product_id=i.product_id,
                product_name=i.product.name if i.product else None,
                product_code=i.product.code if i.product else None,
                product_unit=i.product.unit if i.product else None,
                quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, batch_no=i.batch_no,
            ) for i in t.items],
            notes=t.notes, month_closed=t.month_closed,
        ))

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@router.post("/transactions", response_model=InventoryTransactionResponse)
async def create_transaction(data: InventoryTransactionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await check_month_not_closed(db, data.transaction_date)

    code = await generate_code(db, "inventory_transaction")
    total = Decimal("0")

    txn = InventoryTransaction(
        code=code, transaction_type=data.transaction_type, transaction_date=data.transaction_date,
        supplier_id=data.supplier_id, customer_id=data.customer_id,
        notes=data.notes, created_by=current_user.id,
    )
    db.add(txn)
    await db.flush()

    for item_data in data.items:
        amount = item_data.quantity * item_data.unit_price
        total += amount
        iti = InventoryTransactionItem(
            transaction_id=txn.id, product_id=item_data.product_id,
            quantity=item_data.quantity, unit_price=item_data.unit_price,
            amount=amount, batch_no=item_data.batch_no,
        )
        db.add(iti)

        # Update stock
        stock_result = await db.execute(
            select(InventoryStock).where(InventoryStock.product_id == item_data.product_id).with_for_update()
        )
        stock = stock_result.scalar_one_or_none()
        if stock is None:
            stock = InventoryStock(product_id=item_data.product_id, current_qty=Decimal("0"), avg_unit_cost=Decimal("0"))
            db.add(stock)
            await db.flush()

        if data.transaction_type in ("inbound", "return_inbound"):
            total_value = stock.current_qty * stock.avg_unit_cost + item_data.quantity * item_data.unit_price
            stock.current_qty += item_data.quantity
            if stock.current_qty > 0:
                stock.avg_unit_cost = total_value / stock.current_qty
            stock.last_inbound_date = data.transaction_date
        elif data.transaction_type in ("outbound", "return_supplier", "damage", "loss"):
            stock.current_qty -= item_data.quantity
            stock.last_outbound_date = data.transaction_date
        elif data.transaction_type == "stocktake_adjust":
            stock.current_qty += item_data.quantity  # Can be negative for adjustment

    txn.total_amount = total
    await db.flush()

    result = await db.execute(select(InventoryTransaction).where(InventoryTransaction.id == txn.id))
    txn = result.scalar_one()
    await create_audit_log(db, current_user.id, current_user.username, "create", "inventory_transaction", resource_id=txn.id, resource_code=code)

    return InventoryTransactionResponse(
        id=txn.id, code=txn.code, transaction_type=txn.transaction_type,
        transaction_date=txn.transaction_date,
        supplier_id=txn.supplier_id, supplier_name=txn.supplier.name if txn.supplier else None,
        customer_id=txn.customer_id, customer_name=txn.customer.name if txn.customer else None,
        status=txn.status, total_amount=txn.total_amount,
        items=[InventoryTransactionItemResponse(
            id=i.id, product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            product_code=i.product.code if i.product else None,
            product_unit=i.product.unit if i.product else None,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, batch_no=i.batch_no,
        ) for i in txn.items],
        notes=txn.notes, month_closed=txn.month_closed,
    )


@router.get("/transactions/{txn_id}", response_model=InventoryTransactionResponse)
async def get_transaction(txn_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(InventoryTransaction).where(InventoryTransaction.id == txn_id))
    t = result.scalar_one_or_none()
    if not t:
        raise NotFoundError("库存交易", txn_id)
    return InventoryTransactionResponse(
        id=t.id, code=t.code, transaction_type=t.transaction_type,
        transaction_date=t.transaction_date,
        supplier_id=t.supplier_id, supplier_name=t.supplier.name if t.supplier else None,
        customer_id=t.customer_id, customer_name=t.customer.name if t.customer else None,
        status=t.status, total_amount=t.total_amount,
        items=[InventoryTransactionItemResponse(
            id=i.id, product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            product_code=i.product.code if i.product else None,
            product_unit=i.product.unit if i.product else None,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, batch_no=i.batch_no,
        ) for i in t.items],
        notes=t.notes, month_closed=t.month_closed,
    )


@router.get("/stock", response_model=PageResponse[InventoryStockResponse])
async def list_stock(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.product import Product
    query = select(InventoryStock).join(Product)
    count_query = select(func.count(InventoryStock.id)).join(Product)

    if keyword:
        query = query.where(Product.name.ilike(f"%{keyword}%") | Product.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(Product.name.ilike(f"%{keyword}%") | Product.code.ilike(f"%{keyword}%"))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Product.name).offset((page - 1) * page_size).limit(page_size))
    stocks = result.scalars().all()

    items = [InventoryStockResponse(
        id=s.id, product_id=s.product_id,
        product_name=s.product.name if s.product else None,
        product_code=s.product.code if s.product else None,
        product_unit=s.product.unit if s.product else None,
        category_name=s.product.category.name if s.product and s.product.category else None,
        current_qty=s.current_qty, avg_unit_cost=s.avg_unit_cost,
        last_inbound_date=s.last_inbound_date, last_outbound_date=s.last_outbound_date,
    ) for s in stocks]

    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)
