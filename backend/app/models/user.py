"""
使用者資料模型

儲存 LINE 使用者資訊及相關設定
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order


class User(Base):
    """
    使用者資料表
    
    儲存透過 LINE Login 登入的使用者資訊
    """
    __tablename__ = "users"
    
    # 主鍵
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # LINE 使用者 ID（唯一識別碼）
    line_user_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    # 使用者顯示名稱
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # 使用者頭像 URL
    picture_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 電話號碼
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    # 預設配送地址
    default_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 預設配送地址經緯度（快取用）
    default_latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    default_longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # 使用者角色：user（一般使用者）、admin（管理員）
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
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
    
    # 關聯：使用者的訂單
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="user",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.display_name} ({self.line_user_id})>"
