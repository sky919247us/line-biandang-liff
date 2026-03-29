"""
多層級帳號權限模型

定義角色和權限的關聯
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# 角色-權限關聯表
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id"), primary_key=True),
)


class Role(Base):
    """角色"""
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. "super_admin", "store_manager", "cashier", "kitchen"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 顯示名稱
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # 系統內建角色不可刪除
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    """權限"""
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # e.g. "orders.view", "orders.manage", "products.edit"
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 顯示名稱
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # 權限分類: "orders", "products", "members", "settings"

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
