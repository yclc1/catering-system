"""Product and Product Category API."""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product, ProductCategory
from app.models.purchase import PurchaseOrderItem, PurchaseOrder
from app.core.exceptions import NotFoundError
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse,
    PriceHistoryItem,
)
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.services import generate_code
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/products", tags=["商品管理"])
category_router = APIRouter(prefix="/product-categories", tags=["商品分类"])


# --- Products ---

@router.get("", response_model=PageResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Product).where(Product.is_deleted == False)
    count_query = select(func.count(Product.id)).where(Product.is_deleted == False)

    if keyword:
        query = query.where(Product.name.ilike(f"%{keyword}%") | Product.code.ilike(f"%{keyword}%"))
        count_query = count_query.where(Product.name.ilike(f"%{keyword}%") | Product.code.ilike(f"%{keyword}%"))
    if category_id:
        query = query.where(Product.category_id == category_id)
        count_query = count_query.where(Product.category_id == category_id)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size))
    products = result.scalars().all()

    items = []
    for p in products:
        items.append(ProductResponse(
            id=p.id, code=p.code, name=p.name, category_id=p.category_id,
            category_name=p.category.name if p.category else None,
            unit=p.unit, spec=p.spec,
            default_supplier_id=p.default_supplier_id,
            default_supplier_name=p.default_supplier.name if p.default_supplier else None,
            notes=p.notes,
        ))

    return PageResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    code = await generate_code(db, "product")
    product = Product(code=code, **data.model_dump(), created_by=current_user.id)
    db.add(product)
    await db.flush()

    # Reload with relationships
    result = await db.execute(select(Product).where(Product.id == product.id))
    product = result.scalar_one()

    await create_audit_log(db, current_user.id, current_user.username, "create", "product", resource_id=product.id, resource_code=code)
    return ProductResponse(
        id=product.id, code=product.code, name=product.name, category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        unit=product.unit, spec=product.spec,
        default_supplier_id=product.default_supplier_id,
        default_supplier_name=product.default_supplier.name if product.default_supplier else None,
        notes=product.notes,
    )


@router.get("/dropdown", response_model=list[DropdownItem])
async def product_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.is_deleted == False).order_by(Product.name))
    return [DropdownItem(id=p.id, name=f"{p.name} ({p.unit})", code=p.code) for p in result.scalars().all()]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_deleted == False))
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("商品", product_id)
    return ProductResponse(
        id=p.id, code=p.code, name=p.name, category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        unit=p.unit, spec=p.spec,
        default_supplier_id=p.default_supplier_id,
        default_supplier_name=p.default_supplier.name if p.default_supplier else None,
        notes=p.notes,
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_deleted == False))
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("商品", product_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    p.updated_by = current_user.id
    await db.flush()

    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one()
    return ProductResponse(
        id=p.id, code=p.code, name=p.name, category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        unit=p.unit, spec=p.spec,
        default_supplier_id=p.default_supplier_id,
        default_supplier_name=p.default_supplier.name if p.default_supplier else None,
        notes=p.notes,
    )


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_deleted == False))
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("商品", product_id)

    p.is_deleted = True
    p.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="商品已删除")


@router.get("/{product_id}/price-history", response_model=list[PriceHistoryItem])
async def get_price_history(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get historical purchase prices for a product."""
    result = await db.execute(
        select(PurchaseOrderItem, PurchaseOrder)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .where(
            PurchaseOrderItem.product_id == product_id,
            PurchaseOrder.status == "confirmed",
        )
        .order_by(PurchaseOrder.order_date.desc())
        .limit(100)
    )
    rows = result.all()
    items = []
    for item, po in rows:
        items.append(PriceHistoryItem(
            date=po.order_date.isoformat(),
            unit_price=item.unit_price,
            supplier_name=po.supplier.name if po.supplier else None,
        ))
    return items


# --- Product Categories ---

@category_router.get("", response_model=list[ProductCategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.is_deleted == False).order_by(ProductCategory.sort_order)
    )
    return [ProductCategoryResponse.model_validate(c) for c in result.scalars().all()]


@category_router.post("", response_model=ProductCategoryResponse)
async def create_category(
    data: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = ProductCategory(**data.model_dump(), created_by=current_user.id)
    db.add(cat)
    await db.flush()
    return ProductCategoryResponse.model_validate(cat)


@category_router.put("/{cat_id}", response_model=ProductCategoryResponse)
async def update_category(
    cat_id: int, data: ProductCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProductCategory).where(ProductCategory.id == cat_id, ProductCategory.is_deleted == False))
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("商品分类", cat_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    await db.flush()
    return ProductCategoryResponse.model_validate(cat)


@category_router.delete("/{cat_id}", response_model=MessageResponse)
async def delete_category(
    cat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProductCategory).where(ProductCategory.id == cat_id, ProductCategory.is_deleted == False))
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("商品分类", cat_id)
    cat.is_deleted = True
    cat.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="商品分类已删除")


@category_router.get("/dropdown", response_model=list[DropdownItem])
async def category_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.is_deleted == False).order_by(ProductCategory.sort_order)
    )
    return [DropdownItem(id=c.id, name=c.name) for c in result.scalars().all()]
