"""
訂單服務

處理訂單通知推播和業務驗證邏輯。
訂單 CRUD 操作由 app.api.v1.orders 和 app.api.v1.admin.orders 直接處理。
"""
from datetime import datetime
from typing import Optional

from app.services.line_messaging import (
    line_messaging,
    create_order_confirmed_message,
    create_order_ready_message,
    create_order_cancelled_message,
    create_delivery_started_message,
)
from app.core.config import settings


async def send_order_status_notification(
    user_line_id: str,
    order_number: str,
    status: str,
    total: int = 0,
    pickup_time: Optional[str] = None,
    cancelled_reason: Optional[str] = None,
) -> bool:
    """
    發送訂單狀態通知

    根據訂單狀態發送對應的 LINE 訊息
    """
    message = None

    if status == "confirmed":
        message = create_order_confirmed_message(order_number, total, pickup_time)
    elif status == "ready":
        message = create_order_ready_message(order_number)
    elif status == "delivering":
        estimated_time = datetime.now().strftime("%H:%M")
        message = create_delivery_started_message(order_number, estimated_time)
    elif status == "cancelled":
        message = create_order_cancelled_message(order_number, cancelled_reason)

    if message:
        return await line_messaging.push_message(user_line_id, [message])

    return True


def get_store_settings():
    """取得管理後台的店家設定（若已載入）"""
    try:
        from app.api.v1.admin.settings import STORE_SETTINGS
        return STORE_SETTINGS
    except Exception:
        return None


def validate_business_hours() -> tuple[bool, str]:
    """
    檢查是否在營業時間內

    優先使用管理後台設定，否則使用 config 預設值

    Returns:
        (是否在營業時間, 錯誤訊息)
    """
    now = datetime.now()

    # 取得設定
    store = get_store_settings()
    open_time = store["open_time"] if store else settings.business_hours_start
    close_time = store["close_time"] if store else settings.business_hours_end
    closed_days = store.get("closed_days", []) if store else []

    # 檢查公休日
    day_map = {
        0: "monday", 1: "tuesday", 2: "wednesday",
        3: "thursday", 4: "friday", 5: "saturday", 6: "sunday",
    }
    today_name = day_map.get(now.weekday(), "")
    if today_name in closed_days:
        return False, "今日公休，請於營業日再訂購"

    # 解析營業時間
    start_h, start_m = map(int, open_time.split(":"))
    end_h, end_m = map(int, close_time.split(":"))

    current_minutes = now.hour * 60 + now.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if current_minutes < start_minutes or current_minutes > end_minutes:
        return False, f"目前不在營業時間內（{open_time} - {close_time}）"

    return True, ""
