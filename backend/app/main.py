"""
FastAPI 主應用程式

LINE LIFF 便當訂購系統後端服務入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.core.middleware import PerformanceMiddleware
from app.api.v1 import auth, products, orders
from app.api.v1.admin import admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理
    
    啟動時初始化資料庫，關閉時進行清理
    """
    # 設定日誌
    setup_logging()
    
    # 啟動時
    init_db()
    yield
    # 關閉時（如有需要的清理工作）


# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.app_name,
    description="LINE LIFF 便當訂購系統 API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 效能監控中間件
app.add_middleware(PerformanceMiddleware)

# CORS 設定
import os
_frontend_url = os.getenv("FRONTEND_URL", "")
_cors_origins = [
    "http://localhost:5173",        # 本地開發
    "http://localhost:3000",
]
if _frontend_url:
    _cors_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# 註冊 API 路由
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(products.router, prefix=settings.api_v1_prefix)
app.include_router(orders.router, prefix=settings.api_v1_prefix)

# 註冊管理後台 API 路由
app.include_router(admin_router, prefix=settings.api_v1_prefix)

# 註冊 LINE Webhook 路由
from app.api.v1 import webhook
app.include_router(webhook.router, prefix=settings.api_v1_prefix)

# 註冊配送 API 路由
from app.api.v1 import delivery
app.include_router(delivery.router, prefix=settings.api_v1_prefix)

# 註冊優惠券 API 路由
from app.api.v1 import coupons
app.include_router(coupons.router, prefix=settings.api_v1_prefix)

# 註冊監控 API 路由
from app.api.v1 import monitoring
app.include_router(monitoring.router, prefix=settings.api_v1_prefix)

# 註冊會員點數 API 路由
from app.api.v1 import loyalty
app.include_router(loyalty.router, prefix=settings.api_v1_prefix)

# 註冊群組點餐 API 路由
from app.api.v1 import group_orders
app.include_router(group_orders.router, prefix=settings.api_v1_prefix)

# 註冊集點卡 API 路由
from app.api.v1 import stamp_cards
app.include_router(stamp_cards.router, prefix=settings.api_v1_prefix)

# 註冊推薦好友 API 路由
from app.api.v1 import referrals
app.include_router(referrals.router, prefix=settings.api_v1_prefix)


# 根路徑
@app.get("/", tags=["系統"])
async def root():
    """
    API 根路徑
    """
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else None
    }


# 健康檢查端點
@app.get("/ping", tags=["系統"])
async def ping():
    """極簡保活端點，供 cron-job 使用"""
    return "ok"


@app.get("/health", tags=["系統"])
async def health_check():
    """
    健康檢查端點
    
    用於負載均衡器和監控服務確認應用程式狀態
    """
    from sqlalchemy import text
    from app.core.database import SessionLocal
    
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "checks": {}
    }
    
    # 檢查資料庫連線
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status

