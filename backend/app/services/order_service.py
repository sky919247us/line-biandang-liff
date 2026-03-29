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


def validate_business_hours() -> tuple[bool, str]:
    """
    檢查是否在營業時間內

    Returns:
        (是否在營業時間, 錯誤訊息)
    """
    now = datetime.now()

    # 週末不營業
    if now.weekday() >= 5:
        return False, "週末公休，請於平日訂購"

    # 解析營業時間設定
    start_h, start_m = map(int, settings.business_hours_start.split(":"))
    end_h, end_m = map(int, settings.business_hours_end.split(":"))

    current_minutes = now.hour * 60 + now.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if current_minutes < start_minutes or current_minutes > end_minutes:
        return False, f"目前不在營業時間內（{settings.business_hours_start} - {settings.business_hours_end}）"

    return True, ""
