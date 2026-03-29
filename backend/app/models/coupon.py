"""
優惠券資料模型

定義優惠券類型、規則和使用記錄
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, DateTime, Numeric, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class CouponType(str, Enum):
    """優惠券類型"""
    FIXED = "fixed"           # 固定金額折扣
    PERCENTAGE = "percentage"  # 百分比折扣
    FREE_DELIVERY = "free_delivery"  # 免運費
    ORDER_THRESHOLD = "order_threshold"  # 滿額折扣 - 訂單滿額時自動套用
    FIRST_PURCHASE = "first_purchase"    # 首購折扣 - 首次購買自動套用


class Coupon(Base):
    """
    優惠券資料表
    
    定義優惠券的基本資訊和使用規則
    """
    __tablename__ = "coupons"
    
    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 優惠券代碼（唯一）
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    # 優惠券名稱
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 優惠券類型
    coupon_type: Mapped[str] = mapped_column(
        String(20),
        default=CouponType.FIXED.value,
        nullable=False
    )
    
    # 折扣值（固定金額或百分比）
    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    
    # 最低消費金額
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    
    # 最高折扣金額（百分比折扣時使用）
    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    
    # 使用次數限制（0 表示無限制）
    usage_limit: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # 每人使用次數限制（0 表示無限制）
    per_user_limit: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    
    # 已使用次數
    used_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # 有效期間
    valid_from: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    
    valid_until: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    
    # 是否自動套用（無需輸入代碼）
    is_auto_apply: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 是否僅限首次購買
    first_purchase_only: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 是否啟用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    
    # 關聯：使用記錄
    usages: Mapped[List["CouponUsage"]] = relationship(
        "CouponUsage",
        back_populates="coupon",
        lazy="dynamic"
    )
    
    @property
    def is_valid(self) -> bool:
        """檢查優惠券是否在有效期內且可使用"""
        now = datetime.now()
        
        if not self.is_active:
            return False
        
        if now < self.valid_from or now > self.valid_until:
            return False
        
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False
        
        return True
    
    @property
    def remaining_usage(self) -> Optional[int]:
        """剩餘可使用次數"""
        if self.usage_limit == 0:
            return None  # 無限制
        return max(0, self.usage_limit - self.used_count)
    
    def calculate_discount(self, order_total: Decimal) -> Decimal:
        """
        計算折扣金額
        
        Args:
            order_total: 訂單金額
            
        Returns:
            折扣金額
        """
        if order_total < self.min_order_amount:
            return Decimal("0")
        
        if self.coupon_type == CouponType.FIXED.value:
            # 固定金額折扣
            return min(self.discount_value, order_total)
        
        elif self.coupon_type == CouponType.PERCENTAGE.value:
            # 百分比折扣
            discount = order_total * self.discount_value / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount.quantize(Decimal("0.01"))
        
        elif self.coupon_type == CouponType.ORDER_THRESHOLD.value:
            # 滿額折扣：訂單金額達門檻時，給予固定金額折扣
            if order_total >= self.min_order_amount:
                return min(self.discount_value, order_total)
            return Decimal("0")

        elif self.coupon_type == CouponType.FIRST_PURCHASE.value:
            # 首購折扣：固定金額折扣（首購資格由服務層檢查）
            return min(self.discount_value, order_total)

        elif self.coupon_type == CouponType.FREE_DELIVERY.value:
            # 免運費（由訂單處理邏輯處理）
            return Decimal("0")

        return Decimal("0")
    
    def __repr__(self) -> str:
        return f"<Coupon {self.code}: {self.name}>"


class CouponUsage(Base):
    """
    優惠券使用記錄資料表
    
    記錄每次優惠券的使用情況
    """
    __tablename__ = "coupon_usages"
    
    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 優惠券 ID
    coupon_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("coupons.id"),
        nullable=False,
        index=True
    )
    
    # 使用者 ID
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    
    # 訂單 ID
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )
    
    # 折扣金額
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    # 使用時間
    used_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    
    # 關聯
    coupon: Mapped["Coupon"] = relationship(
        "Coupon",
        back_populates="usages"
    )
    
    user: Mapped["User"] = relationship("User")
    order: Mapped["Order"] = relationship("Order")
    
    def __repr__(self) -> str:
        return f"<CouponUsage {self.coupon_id} by {self.user_id}>"
