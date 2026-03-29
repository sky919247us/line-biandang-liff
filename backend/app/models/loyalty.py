"""
會員點數資料模型

儲存會員點數帳戶及交易紀錄
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class LoyaltyAccount(Base):
    """
    會員點數帳戶

    每位使用者一個點數帳戶，記錄點數餘額與會員等級
    """
    __tablename__ = "loyalty_accounts"

    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 使用者 ID（外鍵）
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # 點數餘額
    points_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 累計獲得點數
    total_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 累計兌換點數
    total_redeemed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 會員等級：normal, silver, gold, vip
    tier: Mapped[str] = mapped_column(
        String(20),
        default="normal",
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

    # 關聯
    user = relationship("User", backref="loyalty_account", uselist=False)
    transactions: Mapped[List["PointTransaction"]] = relationship(
        "PointTransaction",
        back_populates="loyalty_account",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<LoyaltyAccount user={self.user_id} points={self.points_balance} tier={self.tier}>"


class PointTransaction(Base):
    """
    點數交易紀錄

    記錄每一筆點數的獲得、兌換、獎勵、過期或調整
    """
    __tablename__ = "point_transactions"

    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 點數帳戶 ID（外鍵）
    loyalty_account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("loyalty_accounts.id"),
        nullable=False,
        index=True
    )

    # 關聯訂單 ID（可選）
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("orders.id"),
        nullable=True
    )

    # 點數數量（正數為獲得，負數為兌換）
    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # 交易類型：earn（獲得）、redeem（兌換）、bonus（獎勵）、expire（過期）、adjust（調整）
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # 交易說明
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # 關聯
    loyalty_account: Mapped["LoyaltyAccount"] = relationship(
        "LoyaltyAccount",
        back_populates="transactions"
    )

    def __repr__(self) -> str:
        return f"<PointTransaction type={self.transaction_type} points={self.points}>"
