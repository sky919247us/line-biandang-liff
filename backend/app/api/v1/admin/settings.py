"""
管理後台 - 系統設定 API

提供店家設定管理功能
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentAdmin

router = APIRouter(prefix="/settings", tags=["Admin - Settings"])


# ==================== Schemas ====================

class StoreSettingsSchema(BaseModel):
    """店家設定 Schema"""
    store_name: str
    phone: str
    address: str
    open_time: str
    close_time: str
    closed_days: list[str]
    delivery_enabled: bool
    delivery_fee: int
    free_delivery_minimum: int
    delivery_radius: float
    auto_accept_orders: bool


class StoreSettingsUpdateRequest(BaseModel):
    """更新店家設定請求"""
    store_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    closed_days: Optional[list[str]] = None
    delivery_enabled: Optional[bool] = None
    delivery_fee: Optional[int] = None
    free_delivery_minimum: Optional[int] = None
    delivery_radius: Optional[float] = None
    auto_accept_orders: Optional[bool] = None


# ==================== 模擬資料 ====================

STORE_SETTINGS: Dict[str, Any] = {
    "store_name": "一米粒 弁当専門店",
    "phone": "0909-998-952",
    "address": "台中市中區興中街20號",
    "open_time": "10:00",
    "close_time": "16:30",
    "closed_days": ["saturday", "sunday"],
    "delivery_enabled": True,
    "delivery_fee": 30,
    "free_delivery_minimum": 300,
    "delivery_radius": 3.0,
    "auto_accept_orders": False,
}


# ==================== API 端點 ====================

@router.get("", response_model=StoreSettingsSchema)
async def get_settings(admin: CurrentAdmin):
    """
    取得店家設定（需管理員權限）
    """
    return STORE_SETTINGS


@router.patch("", response_model=StoreSettingsSchema)
async def update_settings(request: StoreSettingsUpdateRequest, admin: CurrentAdmin):
    """
    更新店家設定（需管理員權限）
    """
    update_data = request.dict(exclude_unset=True)

    # 在實際實作中，這裡會更新資料庫
    global STORE_SETTINGS
    STORE_SETTINGS = {**STORE_SETTINGS, **update_data}

    return STORE_SETTINGS


@router.get("/operating-hours")
async def get_operating_hours(admin: CurrentAdmin):
    """
    取得營業時間資訊（需管理員權限）
    """
    return {
        "open_time": STORE_SETTINGS["open_time"],
        "close_time": STORE_SETTINGS["close_time"],
        "closed_days": STORE_SETTINGS["closed_days"],
    }


@router.get("/delivery-config")
async def get_delivery_config(admin: CurrentAdmin):
    """
    取得外送設定（需管理員權限）
    """
    return {
        "enabled": STORE_SETTINGS["delivery_enabled"],
        "fee": STORE_SETTINGS["delivery_fee"],
        "free_minimum": STORE_SETTINGS["free_delivery_minimum"],
        "radius": STORE_SETTINGS["delivery_radius"],
    }
