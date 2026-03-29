"""
管理後台 - Server-Sent Events (SSE) 即時推送

提供即時訂單通知和儀表板更新
"""
import asyncio
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func

from app.models.order import Order, OrderStatus
from app.core.database import SessionLocal
from app.api.deps import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sse", tags=["Admin - SSE"])


def get_dashboard_stats(db) -> dict:
    """計算即時儀表板統計"""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    order_count = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.status != OrderStatus.CANCELLED.value
    ).count()

    revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.created_at >= today_start,
        Order.status != OrderStatus.CANCELLED.value
    ).scalar()

    pending = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.status == OrderStatus.PENDING.value
    ).count()

    preparing = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.status == OrderStatus.PREPARING.value
    ).count()

    return {
        "todayOrderCount": order_count,
        "todayRevenue": float(revenue) if revenue else 0,
        "pendingOrders": pending,
        "preparingOrders": preparing,
        "timestamp": datetime.now().isoformat(),
    }


async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    """SSE event generator — pushes dashboard stats every 10 seconds"""
    try:
        while True:
            if await request.is_disconnected():
                break

            db = SessionLocal()
            try:
                stats = get_dashboard_stats(db)
                data = json.dumps(stats, ensure_ascii=False)
                yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"SSE stats error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                db.close()

            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass


@router.get("/dashboard")
async def dashboard_stream(
    request: Request,
    admin=Depends(get_current_admin),
):
    """
    SSE 即時儀表板數據流（需管理員權限）

    每 10 秒推送一次最新統計數據
    """
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
