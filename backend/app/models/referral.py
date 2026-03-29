"""
推薦好友資料模型

儲存推薦紀錄與獎勵資訊
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Referral(Base):
    """
    推薦紀錄

    記錄推薦人與被推薦人的關係及獎勵狀態
    """
    __tablename__ = "referrals"

    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 推薦人 ID（外鍵）
    referrer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # 被推薦人 ID（外鍵）
    referred_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # 推薦碼
    referral_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    # 狀態：pending（待完成）、completed（已完成）、rewarded（已發放獎勵）
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    # 推薦人獎勵類型：points、coupon
    referrer_reward_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )

    # 推薦人獎勵值
    referrer_reward_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 被推薦人獎勵類型：points、coupon
    referred_reward_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )

    # 被推薦人獎勵值
    referred_reward_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 完成時間
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
    referrer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referrer_id]
    )
    referred: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referred_id]
    )

    def __repr__(self) -> str:
        return f"<Referral referrer={self.referrer_id} referred={self.referred_id} status={self.status}>"
