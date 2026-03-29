"""KDS 廚房顯示系統 API"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentAdmin
from app.models.order import Order, OrderStatus
from app.services.line_messaging import (
    line_messaging,
    create_order_ready_message,
)


router = APIRouter(prefix="/kds", tags=["Admin - KDS"])


class KDSOrderItem(BaseModel):
    product_name: str
    quantity: int
    customizations: Optional[list] = None
    notes: Optional[str] = None


class KDSOrder(BaseModel):
    id: str
    order_number: str
    order_type: str
    status: str
    pickup_number: Optional[int] = None
    items: List[KDSOrderItem]
    notes: Optional[str] = None
    created_at: datetime
    elapsed_minutes: int


@router.get("/orders", response_model=List[KDSOrder])
async def get_kds_orders(
    db: DbSession,
    admin: CurrentAdmin,
    status: Optional[str] = None
):
    """取得 KDS 訂單（confirmed + preparing）"""
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)
    else:
        query = query.filter(Order.status.in_([
            OrderStatus.CONFIRMED.value,
            OrderStatus.PREPARING.value
        ]))

    orders = query.order_by(Order.created_at.asc()).all()

    result = []
    now = datetime.now()
    for order in orders:
        elapsed = int((now - order.created_at).total_seconds() / 60)
        items = [
            KDSOrderItem(
                product_name=item.product.name if item.product else f"商品 {item.product_id}",
                quantity=item.quantity,
                customizations=item.customizations,
                notes=item.notes
            )
            for item in order.items
        ]
        result.append(KDSOrder(
            id=order.id,
            order_number=order.order_number,
            order_type=order.order_type,
            status=order.status,
            pickup_number=getattr(order, 'pickup_number', None),
            items=items,
            notes=order.notes,
            created_at=order.created_at,
            elapsed_minutes=elapsed
        ))

    return result


@router.patch("/orders/{order_id}/start")
async def start_preparing(order_id: str, db: DbSession, admin: CurrentAdmin):
    """開始備餐"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    if order.status != OrderStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="只有已確認的訂單可以開始備餐")
    order.status = OrderStatus.PREPARING.value
    db.commit()
    return {"message": "開始備餐", "order_id": order_id}


@router.patch("/orders/{order_id}/ready")
async def mark_ready(order_id: str, db: DbSession, admin: CurrentAdmin):
    """標記備餐完成"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    if order.status != OrderStatus.PREPARING.value:
        raise HTTPException(status_code=400, detail="只有備餐中的訂單可以標記完成")
    order.status = OrderStatus.READY.value
    db.commit()

    # 推播 LINE 通知顧客取餐
    if order.user and order.user.line_user_id:
        message = create_order_ready_message(order.order_number)
        await line_messaging.push_message(order.user.line_user_id, [message])

    return {"message": "備餐完成", "order_id": order_id, "pickup_number": getattr(order, 'pickup_number', None)}
