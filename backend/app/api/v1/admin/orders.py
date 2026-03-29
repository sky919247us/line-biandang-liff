"""
管理後台 - 訂單 API

提供訂單列表、詳情、狀態更新等功能
"""
import io
import csv
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from starlette.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentAdmin
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.services.inventory_service import InventoryService
from app.services.line_messaging import (
    line_messaging,
    create_order_confirmed_message,
    create_order_ready_message,
    create_order_cancelled_message,
    create_delivery_started_message,
)


router = APIRouter(prefix="/orders", tags=["Admin - Orders"])


# ==================== Schemas ====================

class OrderItemSchema(BaseModel):
    """訂單項目 Schema"""
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    customizations: Optional[List[dict]] = None
    notes: Optional[str] = None


class OrderSchema(BaseModel):
    """訂單 Schema"""
    id: str
    order_number: str
    order_type: str
    status: str
    subtotal: float
    delivery_fee: float
    discount: float
    total: float
    delivery_address: Optional[str] = None
    delivery_distance: Optional[float] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    pickup_time: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[OrderItemSchema]
    user_display_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    """訂單列表回應"""
    orders: List[OrderSchema]
    total: int
    page: int
    page_size: int


class UpdateStatusRequest(BaseModel):
    """更新狀態請求"""
    status: str
    notify_customer: bool = True  # 是否通知顧客


class CancelOrderRequest(BaseModel):
    """取消訂單請求"""
    reason: Optional[str] = None
    notify_customer: bool = True


class ManualOrderItemRequest(BaseModel):
    """手動建立訂單 - 項目"""
    product_id: str
    quantity: int = 1
    customizations: Optional[List[dict]] = None
    notes: Optional[str] = None


class ManualOrderRequest(BaseModel):
    """手動建立訂單請求"""
    order_type: str = "pickup"
    items: List[ManualOrderItemRequest]
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None
    table_number: Optional[str] = None


class DashboardStats(BaseModel):
    """總覽統計"""
    today_order_count: int
    today_revenue: float
    pending_orders: int
    preparing_orders: int
    completed_orders: int
    cancelled_orders: int


# ==================== 工具函式 ====================

def _generate_order_number(db) -> str:
    """
    產生訂單編號

    格式：BD + 日期(8碼) + 流水號(4碼)
    例如：BD202602040001
    """
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"BD{today}"

    last_order = db.query(Order).filter(
        Order.order_number.like(f"{prefix}%")
    ).order_by(Order.order_number.desc()).first()

    if last_order:
        last_seq = int(last_order.order_number[-4:])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{prefix}{new_seq:04d}"


# ==================== API 端點 ====================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: DbSession,
    admin: CurrentAdmin  # 需要管理員權限
):
    """
    取得總覽統計資料
    """
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 今日訂單
    today_orders = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.created_at <= today_end
    ).all()
    
    today_count = len(today_orders)
    today_revenue = sum(float(o.total) for o in today_orders if o.status != OrderStatus.CANCELLED.value)
    pending = len([o for o in today_orders if o.status == OrderStatus.PENDING.value])
    preparing = len([o for o in today_orders if o.status == OrderStatus.PREPARING.value])
    completed = len([o for o in today_orders if o.status == OrderStatus.COMPLETED.value])
    cancelled = len([o for o in today_orders if o.status == OrderStatus.CANCELLED.value])
    
    return DashboardStats(
        today_order_count=today_count,
        today_revenue=today_revenue,
        pending_orders=pending,
        preparing_orders=preparing,
        completed_orders=completed,
        cancelled_orders=cancelled,
    )


@router.get("/export")
async def export_orders(
    db: DbSession,
    admin: CurrentAdmin,
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    status_filter: Optional[str] = Query(None, alias="status", description="篩選訂單狀態"),
):
    """
    匯出訂單 CSV

    可依日期範圍和狀態篩選
    """
    query = db.query(Order)

    if start_date:
        query = query.filter(Order.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Order.created_at <= datetime.combine(end_date, datetime.max.time()))
    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.order_by(Order.created_at.desc()).all()

    # 產生 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "order_number", "created_at", "status", "order_type",
        "contact_name", "contact_phone", "items",
        "subtotal", "delivery_fee", "discount", "total"
    ])

    for order in orders:
        items_str = "; ".join(
            f"{item.product.name if item.product else '已刪除商品'} x{item.quantity}"
            for item in order.items
        )
        writer.writerow([
            order.order_number,
            order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
            order.status,
            order.order_type,
            order.contact_name or "",
            order.contact_phone or "",
            items_str,
            float(order.subtotal),
            float(order.delivery_fee),
            float(order.discount),
            float(order.total),
        ])

    output.seek(0)

    # 加上 BOM 以便 Excel 正確顯示中文
    bom = "\ufeff"
    content = bom + output.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=orders_export.csv"}
    )


@router.post("/manual", response_model=OrderSchema, status_code=status.HTTP_201_CREATED)
async def create_manual_order(
    request: ManualOrderRequest,
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    手動建立訂單（電話/現場訂單）

    管理員代為建立訂單，使用管理員的 user_id
    """
    if not request.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="訂單至少需要一個項目"
        )

    # 驗證訂單類型
    valid_types = ["pickup", "delivery", "dine_in"]
    if request.order_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的訂單類型: {request.order_type}"
        )

    # 計算訂單金額
    subtotal = Decimal("0")
    order_items = []

    for item_req in request.items:
        product = db.query(Product).filter(Product.id == item_req.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"商品不存在: {item_req.product_id}"
            )

        unit_price = product.price
        item_subtotal = unit_price * item_req.quantity
        subtotal += item_subtotal

        order_items.append(OrderItem(
            product_id=item_req.product_id,
            quantity=item_req.quantity,
            unit_price=unit_price,
            subtotal=item_subtotal,
            customizations=item_req.customizations,
            notes=item_req.notes,
        ))

    total = subtotal  # 手動訂單不計運費和折扣

    order = Order(
        order_number=_generate_order_number(db),
        user_id=admin.id,
        order_type=request.order_type,
        status=OrderStatus.CONFIRMED.value,
        subtotal=subtotal,
        delivery_fee=Decimal("0"),
        discount=Decimal("0"),
        total=total,
        contact_name=request.contact_name,
        contact_phone=request.contact_phone,
        notes=request.notes,
        table_number=request.table_number,
    )

    db.add(order)
    db.flush()

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    # 更新商品今日銷量
    for item_req in request.items:
        product = db.query(Product).filter(Product.id == item_req.product_id).first()
        if product:
            product.today_sold += item_req.quantity

    db.commit()
    db.refresh(order)

    items = [
        OrderItemSchema(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "已刪除商品",
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            customizations=item.customizations,
            notes=item.notes
        )
        for item in order.items
    ]

    return OrderSchema(
        id=order.id,
        order_number=order.order_number,
        order_type=order.order_type,
        status=order.status,
        subtotal=float(order.subtotal),
        delivery_fee=float(order.delivery_fee),
        discount=float(order.discount),
        total=float(order.total),
        delivery_address=order.delivery_address,
        delivery_distance=float(order.delivery_distance) if order.delivery_distance else None,
        contact_name=order.contact_name,
        contact_phone=order.contact_phone,
        pickup_time=order.pickup_time,
        notes=order.notes,
        items=items,
        user_display_name=order.user.display_name if order.user else None,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("", response_model=OrderListResponse)
async def get_orders(
    db: DbSession,
    admin: CurrentAdmin,  # 需要管理員權限
    status_filter: Optional[str] = Query(None, alias="status", description="篩選訂單狀態"),
    order_type: Optional[str] = Query(None, description="篩選訂單類型"),
    search: Optional[str] = Query(None, description="搜尋（訂單編號、聯絡人姓名、電話）"),
    min_amount: Optional[float] = Query(None, description="最低金額"),
    max_amount: Optional[float] = Query(None, description="最高金額"),
    date_from: Optional[date] = Query(None, description="起始日期"),
    date_to: Optional[date] = Query(None, description="結束日期"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
):
    """
    取得訂單列表

    支援依狀態、訂單類型、關鍵字、金額範圍和日期篩選
    """
    query = db.query(Order)

    # 篩選狀態
    if status_filter:
        query = query.filter(Order.status == status_filter)

    # 篩選訂單類型
    if order_type:
        query = query.filter(Order.order_type == order_type)

    # 搜尋（訂單編號、聯絡人姓名、電話）
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Order.order_number.ilike(search_term)) |
            (Order.contact_name.ilike(search_term)) |
            (Order.contact_phone.ilike(search_term))
        )

    # 金額範圍
    if min_amount is not None:
        query = query.filter(Order.total >= min_amount)
    if max_amount is not None:
        query = query.filter(Order.total <= max_amount)

    # 篩選日期
    if date_from:
        query = query.filter(Order.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Order.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    # 總數
    total = query.count()
    
    # 分頁
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # 轉換為回應格式
    order_list = []
    for order in orders:
        items = [
            OrderItemSchema(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "已刪除商品",
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                subtotal=float(item.subtotal),
                customizations=item.customizations,
                notes=item.notes
            )
            for item in order.items
        ]
        
        order_list.append(OrderSchema(
            id=order.id,
            order_number=order.order_number,
            order_type=order.order_type,
            status=order.status,
            subtotal=float(order.subtotal),
            delivery_fee=float(order.delivery_fee),
            discount=float(order.discount),
            total=float(order.total),
            delivery_address=order.delivery_address,
            delivery_distance=float(order.delivery_distance) if order.delivery_distance else None,
            contact_name=order.contact_name,
            contact_phone=order.contact_phone,
            pickup_time=order.pickup_time,
            notes=order.notes,
            items=items,
            user_display_name=order.user.display_name if order.user else None,
            created_at=order.created_at,
            updated_at=order.updated_at,
        ))
    
    return OrderListResponse(
        orders=order_list,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(
    order_id: str,
    db: DbSession,
    admin: CurrentAdmin  # 需要管理員權限
):
    """
    取得單一訂單詳情
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    
    items = [
        OrderItemSchema(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "已刪除商品",
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            customizations=item.customizations,
            notes=item.notes
        )
        for item in order.items
    ]
    
    return OrderSchema(
        id=order.id,
        order_number=order.order_number,
        order_type=order.order_type,
        status=order.status,
        subtotal=float(order.subtotal),
        delivery_fee=float(order.delivery_fee),
        discount=float(order.discount),
        total=float(order.total),
        delivery_address=order.delivery_address,
        delivery_distance=float(order.delivery_distance) if order.delivery_distance else None,
        contact_name=order.contact_name,
        contact_phone=order.contact_phone,
        pickup_time=order.pickup_time,
        notes=order.notes,
        items=items,
        user_display_name=order.user.display_name if order.user else None,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    request: UpdateStatusRequest,
    db: DbSession,
    admin: CurrentAdmin  # 需要管理員權限
):
    """
    更新訂單狀態
    
    有效狀態: pending, confirmed, preparing, ready, delivering, completed, cancelled
    """
    valid_statuses = [e.value for e in OrderStatus]
    
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的狀態: {request.status}"
        )
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    
    old_status = order.status
    order.status = request.status
    
    db.commit()
    
    # 發送 LINE 通知
    if request.notify_customer and order.user and order.user.line_user_id:
        message = None
        
        if request.status == OrderStatus.CONFIRMED.value:
            message = create_order_confirmed_message(
                order.order_number,
                int(order.total),
                order.pickup_time.strftime("%H:%M") if order.pickup_time else None
            )
        elif request.status == OrderStatus.READY.value:
            message = create_order_ready_message(order.order_number)
        elif request.status == OrderStatus.DELIVERING.value:
            message = create_delivery_started_message(
                order.order_number,
                datetime.now().strftime("%H:%M")
            )
        elif request.status == OrderStatus.CANCELLED.value:
            message = create_order_cancelled_message(order.order_number, None)
        
        if message:
            await line_messaging.push_message(order.user.line_user_id, [message])
    
    return {
        "message": "訂單狀態已更新",
        "order_number": order.order_number,
        "old_status": old_status,
        "new_status": request.status
    }


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    request: CancelOrderRequest,
    db: DbSession,
    admin: CurrentAdmin  # 需要管理員權限
):
    """
    取消訂單
    
    會自動回補庫存
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    
    if order.status == OrderStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="訂單已經取消"
        )
    
    if order.status == OrderStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的訂單無法取消"
        )
    
    # 更新狀態
    order.status = OrderStatus.CANCELLED.value
    order.cancel_reason = request.reason
    
    # 回補庫存
    inventory_service = InventoryService(db)
    inventory_items = [
        {'product_id': item.product_id, 'quantity': item.quantity}
        for item in order.items
    ]
    inventory_service.restore_stock_for_order(inventory_items)
    
    # 回補商品今日銷量
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.today_sold = max(0, product.today_sold - item.quantity)
    
    db.commit()
    
    # 發送 LINE 通知
    if request.notify_customer and order.user and order.user.line_user_id:
        message = create_order_cancelled_message(order.order_number, request.reason)
        await line_messaging.push_message(order.user.line_user_id, [message])
    
    return {
        "message": "訂單已取消",
        "order_number": order.order_number,
        "reason": request.reason
    }
