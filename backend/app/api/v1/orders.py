"""
訂單 API 路由

處理訂單建立、查詢和取消
"""
import logging
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, field_validator

from app.api.deps import DbSession, CurrentUser
from app.models.order import Order, OrderItem, OrderStatus, OrderType
from app.models.product import Product
from app.core.config import settings
from app.services.inventory_service import InventoryService
from app.services.delivery_service import delivery_service
from app.services.coupon_service import CouponService
from app.services.promotion_service import PromotionService


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/orders", tags=["訂單"])


class OrderItemCreate(BaseModel):
    """訂單明細建立請求"""
    product_id: str
    quantity: int
    customizations: Optional[List[dict]] = None
    notes: Optional[str] = None
    
    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("數量必須大於 0")
        return v


class OrderCreate(BaseModel):
    """訂單建立請求"""
    order_type: str  # 'pickup' | 'delivery' | 'dine_in'
    items: List[OrderItemCreate]
    delivery_address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    pickup_time: Optional[datetime] = None
    notes: Optional[str] = None
    table_number: Optional[str] = None
    coupon_code: Optional[str] = None

    @field_validator("order_type")
    @classmethod
    def validate_order_type(cls, v):
        if v not in [OrderType.PICKUP.value, OrderType.DELIVERY.value, OrderType.DINE_IN.value]:
            raise ValueError("訂單類型必須是 pickup、delivery 或 dine_in")
        return v


class OrderItemResponse(BaseModel):
    """訂單明細回應"""
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    customizations: Optional[List[dict]]
    notes: Optional[str]


class OrderResponse(BaseModel):
    """訂單回應"""
    id: str
    order_number: str
    order_type: str
    status: str
    subtotal: float
    delivery_fee: float
    discount: float
    total: float
    delivery_address: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    pickup_time: Optional[datetime]
    notes: Optional[str]
    table_number: Optional[str] = None
    pickup_number: Optional[int] = None
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    """訂單列表回應"""
    items: List[OrderResponse]
    total: int


def generate_order_number(db: DbSession) -> str:
    """
    產生訂單編號
    
    格式：BD + 日期(8碼) + 流水號(4碼)
    例如：BD202602040001
    """
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"BD{today}"
    
    # 查詢今日最後一筆訂單
    last_order = db.query(Order).filter(
        Order.order_number.like(f"{prefix}%")
    ).order_by(Order.order_number.desc()).first()
    
    if last_order:
        last_seq = int(last_order.order_number[-4:])
        new_seq = last_seq + 1
    else:
        new_seq = 1
    
    return f"{prefix}{new_seq:04d}"


def generate_pickup_number(db) -> int:
    """產生今日取餐號碼（每日重置）"""
    from sqlalchemy import func as sqla_func
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())

    max_num = db.query(sqla_func.max(Order.pickup_number)).filter(
        Order.created_at >= today_start
    ).scalar()

    return (max_num or 0) + 1


def get_today_order_count(db: DbSession) -> int:
    """
    取得今日訂單數量
    
    統計今日所有未取消的訂單數量
    """
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    count = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.created_at <= today_end,
        Order.status != OrderStatus.CANCELLED.value
    ).count()
    
    return count


@router.get("/availability")
async def check_order_availability(db: DbSession):
    """
    檢查是否可以接單
    
    回傳今日訂單數量和剩餘可接單數量
    """
    today_count = get_today_order_count(db)
    daily_limit = settings.daily_order_limit
    remaining = max(0, daily_limit - today_count)
    
    return {
        "can_order": remaining > 0,
        "today_count": today_count,
        "daily_limit": daily_limit,
        "remaining": remaining
    }


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreate,
    current_user: CurrentUser,
    db: DbSession
):
    """
    建立訂單
    
    Args:
        request: 訂單建立請求
        current_user: 當前使用者
        db: 資料庫會話
        
    Returns:
        OrderResponse: 建立的訂單
    """
    # 檢查每日訂單上限
    today_count = get_today_order_count(db)
    if today_count >= settings.daily_order_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"今日訂單已達上限（{settings.daily_order_limit} 筆），請明日再訂購"
        )
    
    # 驗證訂單內容
    if not request.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="訂單必須包含至少一項商品"
        )
    
    # 外送訂單需要地址
    if request.order_type == OrderType.DELIVERY.value:
        if not request.delivery_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外送訂單需要填寫配送地址"
            )
        if not request.contact_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外送訂單需要填寫聯絡電話"
            )
    
    # 計算訂單金額
    subtotal = Decimal("0")
    order_items = []
    
    for item_data in request.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"商品 {item_data.product_id} 不存在"
            )
        
        if not product.can_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"商品「{product.name}」目前無法訂購"
            )
        
        # 計算客製化加價
        customization_price = Decimal("0")
        if item_data.customizations:
            for custom in item_data.customizations:
                customization_price += Decimal(str(custom.get("price", 0)))
        
        unit_price = product.price + customization_price
        item_subtotal = unit_price * item_data.quantity
        subtotal += item_subtotal
        
        order_items.append({
            "product": product,
            "quantity": item_data.quantity,
            "unit_price": unit_price,
            "subtotal": item_subtotal,
            "customizations": item_data.customizations,
            "notes": item_data.notes
        })
    
    # 計算運費（外送訂單）
    delivery_fee = Decimal("0")
    delivery_distance = None
    
    if request.order_type == OrderType.DELIVERY.value:
        # 使用配送服務計算運費
        delivery_result = await delivery_service.validate_delivery_address(
            request.delivery_address
        )
        
        if not delivery_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=delivery_result.error_message or "配送地址無效"
            )
        
        delivery_distance = delivery_result.distance_km
        
        # 滿額免運邏輯（滿 300 免運）
        free_delivery_threshold = Decimal("300")
        if subtotal >= free_delivery_threshold:
            delivery_fee = Decimal("0")
        else:
            delivery_fee = Decimal(str(delivery_result.delivery_fee))
        
        # 檢查最低消費
        if subtotal < Decimal(str(settings.min_order_amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"外送訂單最低消費 ${settings.min_order_amount}"
            )
    
    # 計算折扣（優惠券）
    discount = Decimal("0")
    coupon_id = None
    coupon_validation = None

    if request.coupon_code:
        coupon_service = CouponService(db)
        coupon_validation = coupon_service.validate_coupon(
            code=request.coupon_code,
            user_id=current_user.id,
            order_subtotal=subtotal,
            order_type=request.order_type
        )
        if not coupon_validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=coupon_validation.error_message or "優惠券無效"
            )
        discount = coupon_validation.discount_amount
        coupon_id = coupon_validation.coupon.id
        # 免運費優惠券
        if coupon_validation.is_free_delivery:
            delivery_fee = Decimal("0")
    else:
        # 未提供優惠券代碼時，嘗試自動套用最佳促銷優惠券
        promotion_service = PromotionService(db)
        auto_coupon = promotion_service.get_best_auto_coupon(
            user_id=current_user.id,
            order_total=subtotal
        )
        if auto_coupon:
            discount = auto_coupon.calculate_discount(subtotal)
            coupon_id = auto_coupon.id

    total = subtotal + delivery_fee - discount

    # 判斷是否自動接單
    from app.api.v1.admin.settings import STORE_SETTINGS
    initial_status = OrderStatus.PENDING.value
    if STORE_SETTINGS.get("auto_accept_orders", False):
        initial_status = OrderStatus.CONFIRMED.value

    # 產生取餐號碼
    pickup_number = generate_pickup_number(db)

    # 建立訂單
    order = Order(
        order_number=generate_order_number(db),
        user_id=current_user.id,
        order_type=request.order_type,
        status=initial_status,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        total=total,
        delivery_address=request.delivery_address,
        delivery_distance=delivery_distance,  # 記錄配送距離
        contact_name=request.contact_name or current_user.display_name,
        contact_phone=request.contact_phone or current_user.phone,
        pickup_time=request.pickup_time,
        notes=request.notes,
        table_number=request.table_number,
        coupon_id=coupon_id,
        pickup_number=pickup_number
    )
    
    db.add(order)
    db.flush()  # 取得 order.id

    # 記錄優惠券使用
    if coupon_id and coupon_validation:
        coupon_service = CouponService(db)
        coupon_service.apply_coupon(
            coupon_id=coupon_id,
            user_id=current_user.id,
            order_id=order.id,
            discount_amount=discount
        )

    # 建立訂單明細
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"],
            customizations=item_data["customizations"],
            notes=item_data["notes"]
        )
        db.add(order_item)
        
        # 更新商品今日銷量
        item_data["product"].today_sold += item_data["quantity"]
    
    # 扣減庫存（依 BOM 扣減物料）
    inventory_service = InventoryService(db)
    inventory_items = [
        {'product_id': item['product'].id, 'quantity': item['quantity']}
        for item in order_items
    ]
    deduction_result = inventory_service.deduct_stock_for_order(inventory_items)
    
    if not deduction_result.success:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=deduction_result.error_message or "庫存扣減失敗"
        )
    
    # 記錄低庫存警示
    if deduction_result.low_stock_alerts:
        for alert in deduction_result.low_stock_alerts:
            logger.warning(
                f"低庫存警示: {alert['name']} 剩餘 {alert['current_stock']} {alert['unit']}, "
                f"安全庫存: {alert['safety_stock']} {alert['unit']}"
            )
    
    db.commit()
    db.refresh(order)
    
    # 建立回應
    items_response = [
        OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            customizations=item.customizations,
            notes=item.notes
        )
        for item in order.items
    ]
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        order_type=order.order_type,
        status=order.status,
        subtotal=float(order.subtotal),
        delivery_fee=float(order.delivery_fee),
        discount=float(order.discount),
        total=float(order.total),
        delivery_address=order.delivery_address,
        contact_name=order.contact_name,
        contact_phone=order.contact_phone,
        pickup_time=order.pickup_time,
        notes=order.notes,
        table_number=order.table_number,
        pickup_number=getattr(order, 'pickup_number', None),
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("", response_model=OrderListResponse)
async def get_orders(
    current_user: CurrentUser,
    db: DbSession,
    status_filter: Optional[str] = Query(None, description="訂單狀態過濾"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    取得使用者訂單列表
    
    Args:
        current_user: 當前使用者
        db: 資料庫會話
        status_filter: 狀態過濾（可選）
        skip: 分頁偏移量
        limit: 取得數量
        
    Returns:
        OrderListResponse: 訂單列表
    """
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    total = query.count()
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    items = []
    for order in orders:
        items_response = [
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                subtotal=float(item.subtotal),
                customizations=item.customizations,
                notes=item.notes
            )
            for item in order.items
        ]
        
        items.append(OrderResponse(
            id=order.id,
            order_number=order.order_number,
            order_type=order.order_type,
            status=order.status,
            subtotal=float(order.subtotal),
            delivery_fee=float(order.delivery_fee),
            discount=float(order.discount),
            total=float(order.total),
            delivery_address=order.delivery_address,
            contact_name=order.contact_name,
            contact_phone=order.contact_phone,
            pickup_time=order.pickup_time,
            notes=order.notes,
            table_number=order.table_number,
            items=items_response,
            created_at=order.created_at,
            updated_at=order.updated_at
        ))
    
    return OrderListResponse(items=items, total=total)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: CurrentUser,
    db: DbSession
):
    """
    取得訂單詳情
    
    Args:
        order_id: 訂單 ID
        current_user: 當前使用者
        db: 資料庫會話
        
    Returns:
        OrderResponse: 訂單詳情
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )
    
    items_response = [
        OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            customizations=item.customizations,
            notes=item.notes
        )
        for item in order.items
    ]
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        order_type=order.order_type,
        status=order.status,
        subtotal=float(order.subtotal),
        delivery_fee=float(order.delivery_fee),
        discount=float(order.discount),
        total=float(order.total),
        delivery_address=order.delivery_address,
        contact_name=order.contact_name,
        contact_phone=order.contact_phone,
        pickup_time=order.pickup_time,
        notes=order.notes,
        table_number=order.table_number,
        pickup_number=getattr(order, 'pickup_number', None),
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.patch("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: CurrentUser,
    db: DbSession,
    reason: Optional[str] = None
):
    """
    取消訂單
    
    只有待確認狀態的訂單可以取消
    
    Args:
        order_id: 訂單 ID
        current_user: 當前使用者
        db: 資料庫會話
        reason: 取消原因（可選）
        
    Returns:
        dict: 取消結果
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )
    
    # 只有待確認狀態可以取消
    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待確認狀態的訂單可以取消"
        )
    
    order.status = OrderStatus.CANCELLED.value
    order.cancel_reason = reason
    
    # 回補庫存（依 BOM 回補物料）
    inventory_service = InventoryService(db)
    inventory_items = [
        {'product_id': item.product_id, 'quantity': item.quantity}
        for item in order.items
    ]
    restore_result = inventory_service.restore_stock_for_order(inventory_items)
    
    if not restore_result.success:
        logger.error(f"訂單 {order.order_number} 取消時庫存回補失敗")
    
    # 回補商品今日銷量
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.today_sold = max(0, product.today_sold - item.quantity)
    
    db.commit()
    
    return {"message": "訂單已取消", "order_number": order.order_number}
