"""
監控 API

提供系統健康檢查、效能統計和監控端點
"""
import os
import platform
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import DbSession, CurrentAdmin
from app.core.config import settings


router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# ==================== Schemas ====================

class SystemInfoSchema(BaseModel):
    """系統資訊"""
    service_name: str
    version: str
    environment: str
    python_version: str
    platform: str
    uptime_seconds: Optional[float] = None


class DatabaseHealthSchema(BaseModel):
    """資料庫健康狀態"""
    status: str
    latency_ms: float
    connection_pool_size: Optional[int] = None


class HealthCheckSchema(BaseModel):
    """健康檢查結果"""
    status: str
    timestamp: datetime
    system: SystemInfoSchema
    database: DatabaseHealthSchema
    checks: dict


# ==================== 全域變數 ====================

# 記錄啟動時間
_start_time = datetime.now()


# ==================== API 端點 ====================

@router.get("/health", response_model=HealthCheckSchema)
async def detailed_health_check(db: DbSession, admin: CurrentAdmin):
    """
    詳細健康檢查（需管理員權限）

    包含系統資訊、資料庫連線狀態等
    """
    import time
    
    # 系統資訊
    system_info = SystemInfoSchema(
        service_name=settings.app_name,
        version="1.0.0",
        environment="production" if not settings.debug else "development",
        python_version=platform.python_version(),
        platform=platform.platform(),
        uptime_seconds=(datetime.now() - _start_time).total_seconds()
    )
    
    # 資料庫健康檢查
    db_start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    db_latency = (time.perf_counter() - db_start) * 1000
    
    database_health = DatabaseHealthSchema(
        status=db_status,
        latency_ms=round(db_latency, 2)
    )
    
    # 整體狀態
    overall_status = "healthy" if db_status == "ok" else "unhealthy"
    
    # 其他檢查項目
    checks = {
        "line_configured": bool(settings.line_channel_id),
        "debug_mode": settings.debug
    }
    
    return HealthCheckSchema(
        status=overall_status,
        timestamp=datetime.now(),
        system=system_info,
        database=database_health,
        checks=checks
    )


@router.get("/stats")
async def get_performance_stats(admin: CurrentAdmin):
    """
    取得效能統計
    
    需要管理員權限
    """
    from app.main import app
    
    # 嘗試取得統計中間件
    stats_middleware = None
    for middleware in app.middleware_stack.app.middleware:
        if hasattr(middleware, "get_stats"):
            stats_middleware = middleware
            break
    
    if stats_middleware:
        return {
            "overview": stats_middleware.get_stats(),
            "endpoints": stats_middleware.get_endpoint_stats()
        }
    
    return {
        "message": "效能統計尚未啟用",
        "hint": "請在 main.py 中加入 RequestStatsMiddleware"
    }


@router.get("/info")
async def get_system_info(admin: CurrentAdmin):
    """
    取得系統資訊（需管理員權限）
    """
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": "production" if not settings.debug else "development",
        "uptime_seconds": (datetime.now() - _start_time).total_seconds()
    }


@router.get("/ready")
async def readiness_check(db: DbSession):
    """
    就緒檢查
    
    用於 Kubernetes 或負載均衡器的就緒探測
    """
    try:
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/live")
async def liveness_check():
    """
    存活檢查
    
    用於 Kubernetes 的存活探測
    """
    return {"alive": True}
