"""Aggregate all API routers."""
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as user_router, role_router, perm_router as permission_router
from app.api.suppliers import router as supplier_router
from app.api.products import router as product_router, category_router as product_category_router
from app.api.customers import router as customer_router
from app.api.meals import router as meal_router
from app.api.settlements import router as settlement_router
from app.api.purchases import router as purchase_router
from app.api.inventory import router as inventory_router
from app.api.accounts import router as account_router, payment_router
from app.api.reconciliation import router as reconciliation_router
from app.api.expenses import router as expense_router, category_router as expense_category_router
from app.api.vehicles import router as vehicle_router
from app.api.contracts import router as contract_router
from app.api.statistics import router as statistics_router
from app.api.audit import audit_router, monthly_close_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(role_router)
api_router.include_router(permission_router)
api_router.include_router(supplier_router)
api_router.include_router(product_router)
api_router.include_router(product_category_router)
api_router.include_router(customer_router)
api_router.include_router(meal_router)
api_router.include_router(settlement_router)
api_router.include_router(purchase_router)
api_router.include_router(inventory_router)
api_router.include_router(account_router)
api_router.include_router(payment_router)
api_router.include_router(reconciliation_router)
api_router.include_router(expense_router)
api_router.include_router(expense_category_router)
api_router.include_router(vehicle_router)
api_router.include_router(contract_router)
api_router.include_router(statistics_router)
api_router.include_router(audit_router)
api_router.include_router(monthly_close_router)
