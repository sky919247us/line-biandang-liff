"""
訂單資料模型

定義訂單和訂單明細
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


class OrderType(str, Enum):
    """訂單類型"""
    PICKUP = "pickup"    # 自取
    DELIVERY = "delivery"  # 外送
    DINE_IN = "dine_in"  # 內用


class OrderStatus(str, Enum):
    """訂單狀態"""
    PENDING = "pending"        # 待確認
    CONFIRMED = "confirmed"    # 已確認
    PREPARING = "preparing"    # 備餐中
    READY = "ready"            # 待取餐
    DELIVERING = "delivering"  # 配送中
    COMPLETED = "completed"    # 已完成
    CANCELLED = "cancelled"    # 已取消


class Order(Base):
    """
    訂單資料表
    """
    __tablename__ = "orders"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 訂單編號（顯示用，如 BD202602040001）
    order_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    
    # 使用者
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # 訂單類型（自取/外送）
    order_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OrderType.PICKUP.value
    )
    
    # 訂單狀態
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OrderStatus.PENDING.value,
        index=True
    )
    
    # 金額
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    # 桌號（內用訂單用）
    table_number: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )

    # 優惠券
    coupon_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("coupons.id"),
        nullable=True
    )

    # 配送資訊（外送用）
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    delivery_latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    delivery_longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    delivery_distance: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # 聯絡人資訊
    contact_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    # 備註
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 預計取餐/配送時間
    pickup_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # 實際完成時間
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # 取餐號碼（每日重設）
    pickup_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # 取消原因
    cancel_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 關聯
    user: Mapped["User"] = relationship(
        "User",
        back_populates="orders"
    )
    
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Order {self.order_number} ({self.status})>"


class OrderItem(Base):
    """
    訂單明細資料表
    """
    __tablename__ = "order_items"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 訂單
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id"),
        nullable=False
    )
    
    # 商品
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=False
    )
    
    # 數量
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    
    # 單價（下單時的價格，避免商品價格變更影響歷史訂單）
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    # 小計
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    # 客製化選項（JSON 格式儲存）
    # 範例: [{"id": "xxx", "name": "加辣", "price": 0}, {"id": "yyy", "name": "加蛋", "price": 10}]
    customizations: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # 備註
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 關聯
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="items"
    )
    
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="order_items"
    )
    
    def __repr__(self) -> str:
        return f"<OrderItem {self.product_id} x{self.quantity}>"
