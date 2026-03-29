"""
管理後台 API 模組

整合所有管理後台 API 路由
"""
from fastapi import APIRouter

from app.api.v1.admin.orders import router as orders_router
from app.api.v1.admin.products import router as products_router
from app.api.v1.admin.inventory import router as inventory_router
from app.api.v1.admin.settings import router as settings_router
from app.api.v1.admin.reports import router as reports_router
from app.api.v1.admin.coupons import router as coupons_router
from app.api.v1.admin.kds import router as kds_router
from app.api.v1.admin.members import router as members_router
from app.api.v1.admin.sse import router as sse_router
from app.api.v1.admin.broadcast import router as broadcast_router
from app.api.v1.admin.rich_menu import router as rich_menu_router

# 建立管理後台主路由
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# 掛載各個子路由
admin_router.include_router(orders_router)
admin_router.include_router(products_router)
admin_router.include_router(inventory_router)
admin_router.include_router(settings_router)
admin_router.include_router(reports_router)
admin_router.include_router(coupons_router)
admin_router.include_router(kds_router)
admin_router.include_router(members_router)
admin_router.include_router(sse_router)
admin_router.include_router(broadcast_router)
admin_router.include_router(rich_menu_router)
