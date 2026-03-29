"""
商品資料模型

定義商品、分類、客製化群組和客製化選項
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Numeric, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.material import ProductMaterial
    from app.models.order import OrderItem


class Category(Base):
    """
    商品分類資料表

    便當分類，如：雞腿類、排骨類、素食類
    """
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 分類名稱
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # 分類描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 排序順序
    sort_order: Mapped[int] = mapped_column(default=0)

    # 是否啟用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # 分類圖片
    image_url: Mapped[Optional[str]] = mapped_column(
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

    # 關聯：此分類下的商品
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Product(Base):
    """
    商品資料表

    便當商品資訊
    """
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 商品名稱
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # 商品描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 價格
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # 促銷價格
    sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    # 促銷起始時間
    sale_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 促銷結束時間
    sale_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 商品圖片 URL
    image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 所屬分類
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("categories.id"),
        nullable=True
    )

    # 是否為套餐組合
    is_combo: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 套餐組合設定（JSON 格式）
    combo_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 供應時段（JSON 格式）
    # 範例: [{"start": "10:00", "end": "14:00", "label": "午餐"}]
    available_periods: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True
    )

    # 是否可供應（庫存足夠時為 True）
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # 是否啟用（手動上下架）
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # 排序順序
    sort_order: Mapped[int] = mapped_column(default=0)

    # 每日限量（0 表示無限制）
    daily_limit: Mapped[int] = mapped_column(default=0)

    # 今日已售數量
    today_sold: Mapped[int] = mapped_column(default=0)

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
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products"
    )

    # 客製化選項
    customization_options: Mapped[List["CustomizationOption"]] = relationship(
        "CustomizationOption",
        back_populates="product",
        lazy="selectin"
    )

    # 客製化群組
    customization_groups: Mapped[List["CustomizationGroup"]] = relationship(
        "CustomizationGroup",
        back_populates="product",
        lazy="selectin"
    )

    # BOM 物料清單
    product_materials: Mapped[List["ProductMaterial"]] = relationship(
        "ProductMaterial",
        back_populates="product",
        lazy="selectin"
    )

    # 訂單明細
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="dynamic"
    )

    @property
    def effective_price(self) -> Decimal:
        """
        取得有效價格

        若目前在促銷期間且有促銷價，回傳促銷價；否則回傳原價
        """
        if self.sale_price is not None and self.sale_start and self.sale_end:
            now = datetime.now()
            if self.sale_start <= now <= self.sale_end:
                return self.sale_price
        return self.price

    @property
    def can_order(self) -> bool:
        """
        檢查是否可訂購

        考慮啟用狀態、庫存狀態和每日限量
        """
        if not self.is_active or not self.is_available:
            return False

        if self.daily_limit > 0 and self.today_sold >= self.daily_limit:
            return False

        return True

    def __repr__(self) -> str:
        return f"<Product {self.name} (${self.price})>"


class CustomizationGroup(Base):
    """
    客製化選項群組

    將客製化選項分組，如：甜度、冰塊、加料
    """
    __tablename__ = "customization_groups"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 所屬商品
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    # 群組名稱（如：甜度、冰塊、加料）
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # 群組類型：single_select（單選）、multi_select（多選）、quantity_select（數量選擇）
    group_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="single_select"
    )

    # 最少選擇數量
    min_select: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 最多選擇數量
    max_select: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    # 排序順序
    sort_order: Mapped[int] = mapped_column(default=0)

    # 是否必選
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 是否啟用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # 關聯
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="customization_groups"
    )

    options: Mapped[List["CustomizationOption"]] = relationship(
        "CustomizationOption",
        back_populates="group",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<CustomizationGroup {self.name}>"


class CustomizationOption(Base):
    """
    商品客製化選項

    如：少飯、加辣、加蛋等選項
    """
    __tablename__ = "customization_options"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 所屬商品
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=False
    )

    # 所屬群組（nullable 以維持向後相容）
    group_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("customization_groups.id", ondelete="SET NULL"),
        nullable=True
    )

    # 選項名稱
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # 選項類型：addon（加購）或 modifier（調整）
    option_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="modifier"
    )

    # 價格調整（加購項目用）
    price_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0
    )

    # 是否為預設選中
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 是否啟用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # 排序順序
    sort_order: Mapped[int] = mapped_column(default=0)

    # 關聯
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="customization_options"
    )

    group: Mapped[Optional["CustomizationGroup"]] = relationship(
        "CustomizationGroup",
        back_populates="options"
    )

    def __repr__(self) -> str:
        return f"<CustomizationOption {self.name}>"
