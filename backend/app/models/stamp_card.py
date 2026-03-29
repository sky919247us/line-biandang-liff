"""
虛擬集點卡資料模型

定義集點卡模板和使用者集點卡
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Numeric, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class StampCardTemplate(Base):
    """
    集點卡模板

    定義集點卡的規則和獎勵
    """
    __tablename__ = "stamp_card_templates"

    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 模板名稱
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 集滿幾個章
    stamps_required: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False
    )

    # 獎勵類型: coupon, free_item, points
    reward_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # 獎勵內容 (JSON: coupon code / product_id / points amount)
    reward_value: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 每次消費滿多少才蓋章
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
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

    def __repr__(self) -> str:
        return f"<StampCardTemplate {self.name}>"


class StampCard(Base):
    """
    使用者的集點卡

    記錄使用者集點進度和獎勵領取狀態
    """
    __tablename__ = "stamp_cards"

    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 使用者 ID
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # 模板 ID
    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stamp_card_templates.id"),
        nullable=False,
        index=True
    )

    # 已蒐集章數
    stamps_collected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 是否已集滿
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 是否已兌換獎勵
    is_reward_claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 集滿時間
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
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
    user: Mapped["User"] = relationship("User")
    template: Mapped["StampCardTemplate"] = relationship("StampCardTemplate")

    def __repr__(self) -> str:
        return f"<StampCard {self.user_id} - {self.template_id}: {self.stamps_collected}>"
