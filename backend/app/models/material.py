"""
物料資料模型

定義物料和 BOM（物料清單）
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Material(Base):
    """
    物料資料表
    
    如：雞腿、排骨、米飯等原物料
    """
    __tablename__ = "materials"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 物料名稱
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    # 物料描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # 單位（如：份、克、個）
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="份"
    )
    
    # 現有庫存
    current_stock: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0
    )
    
    # 安全庫存（低於此值發出警示）
    safety_stock: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0
    )
    
    # 成本單價（用於成本計算）
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0
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
    
    @property
    def is_low_stock(self) -> bool:
        """
        檢查是否低於安全庫存
        """
        return self.current_stock < self.safety_stock
    
    def __repr__(self) -> str:
        return f"<Material {self.name} ({self.current_stock} {self.unit})>"


class ProductMaterial(Base):
    """
    商品物料對應表（BOM）
    
    定義每個商品需要消耗的物料數量
    """
    __tablename__ = "product_materials"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 商品
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=False
    )
    
    # 物料
    material_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("materials.id"),
        nullable=False
    )
    
    # 需要數量
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    # 關聯
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_materials"
    )
    
    material: Mapped["Material"] = relationship(
        "Material"
    )
    
    def __repr__(self) -> str:
        return f"<ProductMaterial {self.product_id} -> {self.material_id} x{self.quantity}>"
