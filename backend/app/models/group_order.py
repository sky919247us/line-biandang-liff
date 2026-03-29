"""群組點餐資料模型"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, Integer, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class GroupOrderStatus(str, Enum):
    OPEN = "open"           # 開放加入
    LOCKED = "locked"       # 已鎖定（不再接受新品項）
    ORDERED = "ordered"     # 已下單
    COMPLETED = "completed" # 已完成
    CANCELLED = "cancelled" # 已取消


class GroupOrder(Base):
    __tablename__ = "group_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=GroupOrderStatus.OPEN.value)
    order_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    share_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    max_participants: Mapped[int] = mapped_column(Integer, default=10)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])
    participants: Mapped[List["GroupOrderParticipant"]] = relationship("GroupOrderParticipant", back_populates="group_order", cascade="all, delete-orphan", lazy="selectin")
    order: Mapped[Optional["Order"]] = relationship("Order")

    @property
    def total_amount(self) -> Decimal:
        return sum((p.subtotal for p in self.participants), Decimal("0"))


class GroupOrderParticipant(Base):
    __tablename__ = "group_order_participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("group_orders.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # [{product_id, product_name, quantity, unit_price, subtotal, customizations, notes}]
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    group_order: Mapped["GroupOrder"] = relationship("GroupOrder", back_populates="participants")
    user: Mapped["User"] = relationship("User")
