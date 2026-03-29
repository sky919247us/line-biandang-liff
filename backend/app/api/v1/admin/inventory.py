"""
管理後台 - 庫存 API

提供物料庫存管理功能
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentAdmin
from app.models.material import Material, ProductMaterial
from app.models.product import Product
from app.services.inventory_service import InventoryService


router = APIRouter(prefix="/inventory", tags=["Admin - Inventory"])


# ==================== Schemas ====================

class MaterialCreateRequest(BaseModel):
    """建立物料請求"""
    name: str
    unit: str = "份"
    current_stock: float = 0
    safety_stock: float = 0
    unit_cost: float = 0
    description: Optional[str] = None


class MaterialSchema(BaseModel):
    """物料 Schema"""
    id: str
    name: str
    description: Optional[str] = None
    unit: str
    current_stock: float
    safety_stock: float
    unit_cost: float
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime


class MaterialUpdateRequest(BaseModel):
    """更新物料請求"""
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    safety_stock: Optional[float] = None
    unit_cost: Optional[float] = None


class StockAdjustmentRequest(BaseModel):
    """庫存調整請求"""
    quantity: float
    reason: Optional[str] = None


class StockSetRequest(BaseModel):
    """設定庫存請求"""
    new_stock: float
    reason: Optional[str] = None


class InventoryStats(BaseModel):
    """庫存統計"""
    total_materials: int
    low_stock_count: int
    out_of_stock_count: int


class LowStockAlertSchema(BaseModel):
    """低庫存警示 Schema"""
    id: str
    name: str
    current_stock: float
    safety_stock: float
    unit: str
    shortage: float


class ProductMaterialSchema(BaseModel):
    """商品物料對應 Schema (BOM)"""
    id: str
    product_id: str
    product_name: str
    material_id: str
    material_name: str
    quantity: float
    unit: str


class BOMCreateRequest(BaseModel):
    """建立 BOM 對應請求"""
    product_id: str
    material_id: str
    quantity: float


class BOMUpdateRequest(BaseModel):
    """更新 BOM 對應請求"""
    quantity: float


# ==================== API 端點 ====================

@router.get("/stats", response_model=InventoryStats)
async def get_inventory_stats(db: DbSession, admin: CurrentAdmin):
    """
    取得庫存統計資料
    """
    materials = db.query(Material).all()
    
    total = len(materials)
    low = len([m for m in materials if 0 < float(m.current_stock) <= float(m.safety_stock)])
    out = len([m for m in materials if float(m.current_stock) <= 0])

    return InventoryStats(
        total_materials=total,
        low_stock_count=low,
        out_of_stock_count=out,
    )


@router.get("/alerts", response_model=List[LowStockAlertSchema])
async def get_low_stock_alerts(db: DbSession, admin: CurrentAdmin):
    """
    取得低庫存警示清單
    """
    inventory_service = InventoryService(db)
    alerts = inventory_service.get_low_stock_materials()
    
    return [
        LowStockAlertSchema(**alert)
        for alert in alerts
    ]


@router.get("", response_model=List[MaterialSchema])
async def get_materials(
    db: DbSession,
    admin: CurrentAdmin,
    low_stock_only: bool = Query(False, description="只顯示低庫存"),
    search: Optional[str] = Query(None, description="搜尋名稱"),
):
    """
    取得物料清單
    """
    query = db.query(Material)

    if search:
        query = query.filter(Material.name.ilike(f"%{search}%"))

    materials = query.order_by(Material.name).all()

    if low_stock_only:
        materials = [m for m in materials if m.is_low_stock]

    return [
        MaterialSchema(
            id=m.id,
            name=m.name,
            description=m.description,
            unit=m.unit,
            current_stock=float(m.current_stock),
            safety_stock=float(m.safety_stock),
            unit_cost=float(m.unit_cost),
            is_low_stock=m.is_low_stock,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in materials
    ]


@router.post("", response_model=MaterialSchema, status_code=status.HTTP_201_CREATED)
async def create_material(db: DbSession, admin: CurrentAdmin, request: MaterialCreateRequest):
    """
    建立新物料
    """
    # 檢查名稱是否重複
    existing = db.query(Material).filter(Material.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="物料名稱已存在"
        )

    material = Material(
        name=request.name,
        description=request.description,
        unit=request.unit,
        current_stock=Decimal(str(request.current_stock)),
        safety_stock=Decimal(str(request.safety_stock)),
        unit_cost=Decimal(str(request.unit_cost)),
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)

    return MaterialSchema(
        id=material.id,
        name=material.name,
        description=material.description,
        unit=material.unit,
        current_stock=float(material.current_stock),
        safety_stock=float(material.safety_stock),
        unit_cost=float(material.unit_cost),
        is_low_stock=material.is_low_stock,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.get("/{material_id}", response_model=MaterialSchema)
async def get_material(db: DbSession, admin: CurrentAdmin, material_id: str):
    """
    取得單一物料詳情
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    return MaterialSchema(
        id=material.id,
        name=material.name,
        description=material.description,
        unit=material.unit,
        current_stock=float(material.current_stock),
        safety_stock=float(material.safety_stock),
        unit_cost=float(material.unit_cost),
        is_low_stock=material.is_low_stock,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.patch("/{material_id}", response_model=MaterialSchema)
async def update_material(db: DbSession, admin: CurrentAdmin, material_id: str, request: MaterialUpdateRequest):
    """
    更新物料資訊
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    if request.name is not None:
        material.name = request.name
    if request.description is not None:
        material.description = request.description
    if request.unit is not None:
        material.unit = request.unit
    if request.safety_stock is not None:
        material.safety_stock = Decimal(str(request.safety_stock))
    if request.unit_cost is not None:
        material.unit_cost = Decimal(str(request.unit_cost))

    db.commit()
    db.refresh(material)

    return MaterialSchema(
        id=material.id,
        name=material.name,
        description=material.description,
        unit=material.unit,
        current_stock=float(material.current_stock),
        safety_stock=float(material.safety_stock),
        unit_cost=float(material.unit_cost),
        is_low_stock=material.is_low_stock,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(db: DbSession, admin: CurrentAdmin, material_id: str):
    """
    刪除物料
    
    注意：若物料有關聯的 BOM，無法刪除
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 檢查是否有關聯的 BOM
    bom_count = db.query(ProductMaterial).filter(
        ProductMaterial.material_id == material_id
    ).count()
    
    if bom_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"此物料有 {bom_count} 個商品關聯，無法刪除"
        )

    db.delete(material)
    db.commit()


@router.post("/{material_id}/adjust", response_model=MaterialSchema)
async def adjust_stock(db: DbSession, admin: CurrentAdmin, material_id: str, request: StockAdjustmentRequest):
    """
    調整庫存數量
    
    正數表示增加（補貨），負數表示減少
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    inventory_service = InventoryService(db)
    
    if request.quantity > 0:
        success = inventory_service.add_material_stock(
            material_id=material_id,
            quantity=Decimal(str(request.quantity)),
            reason=request.reason or "手動補貨"
        )
    else:
        # 負數表示扣減
        new_stock = material.current_stock + Decimal(str(request.quantity))
        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="庫存不能為負數"
            )
        success = inventory_service.update_material_stock(
            material_id=material_id,
            new_stock=new_stock,
            reason=request.reason or "手動扣減"
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="庫存調整失敗"
        )

    db.commit()
    db.refresh(material)

    return MaterialSchema(
        id=material.id,
        name=material.name,
        description=material.description,
        unit=material.unit,
        current_stock=float(material.current_stock),
        safety_stock=float(material.safety_stock),
        unit_cost=float(material.unit_cost),
        is_low_stock=material.is_low_stock,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.post("/{material_id}/set-stock", response_model=MaterialSchema)
async def set_stock(db: DbSession, admin: CurrentAdmin, material_id: str, request: StockSetRequest):
    """
    直接設定庫存數量
    
    用於盤點時直接設定正確庫存
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    if request.new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="庫存不能為負數"
        )

    inventory_service = InventoryService(db)
    success = inventory_service.update_material_stock(
        material_id=material_id,
        new_stock=Decimal(str(request.new_stock)),
        reason=request.reason or "盤點調整"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="庫存設定失敗"
        )

    db.commit()
    db.refresh(material)

    return MaterialSchema(
        id=material.id,
        name=material.name,
        description=material.description,
        unit=material.unit,
        current_stock=float(material.current_stock),
        safety_stock=float(material.safety_stock),
        unit_cost=float(material.unit_cost),
        is_low_stock=material.is_low_stock,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


# ==================== BOM 管理 API ====================

@router.get("/bom/list", response_model=List[ProductMaterialSchema])
async def get_all_bom(
    db: DbSession,
    admin: CurrentAdmin,
    product_id: Optional[str] = Query(None, description="依商品過濾"),
    material_id: Optional[str] = Query(None, description="依物料過濾"),
):
    """
    取得 BOM 對應清單
    """
    query = db.query(ProductMaterial)

    if product_id:
        query = query.filter(ProductMaterial.product_id == product_id)
    if material_id:
        query = query.filter(ProductMaterial.material_id == material_id)

    bom_list = query.all()

    return [
        ProductMaterialSchema(
            id=pm.id,
            product_id=pm.product_id,
            product_name=pm.product.name if pm.product else "未知商品",
            material_id=pm.material_id,
            material_name=pm.material.name if pm.material else "未知物料",
            quantity=float(pm.quantity),
            unit=pm.material.unit if pm.material else "份",
        )
        for pm in bom_list
    ]


@router.post("/bom", response_model=ProductMaterialSchema, status_code=status.HTTP_201_CREATED)
async def create_bom(db: DbSession, admin: CurrentAdmin, request: BOMCreateRequest):
    """
    建立商品物料對應 (BOM)
    """
    # 驗證商品存在
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )

    # 驗證物料存在
    material = db.query(Material).filter(Material.id == request.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物料不存在"
        )

    # 檢查是否已存在相同對應
    existing = db.query(ProductMaterial).filter(
        ProductMaterial.product_id == request.product_id,
        ProductMaterial.material_id == request.material_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此商品已有相同物料對應"
        )

    bom = ProductMaterial(
        product_id=request.product_id,
        material_id=request.material_id,
        quantity=Decimal(str(request.quantity)),
    )
    
    db.add(bom)
    db.commit()
    db.refresh(bom)

    return ProductMaterialSchema(
        id=bom.id,
        product_id=bom.product_id,
        product_name=product.name,
        material_id=bom.material_id,
        material_name=material.name,
        quantity=float(bom.quantity),
        unit=material.unit,
    )


@router.patch("/bom/{bom_id}", response_model=ProductMaterialSchema)
async def update_bom(db: DbSession, admin: CurrentAdmin, bom_id: str, request: BOMUpdateRequest):
    """
    更新 BOM 對應的用量
    """
    bom = db.query(ProductMaterial).filter(ProductMaterial.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 對應不存在")

    bom.quantity = Decimal(str(request.quantity))
    
    db.commit()
    db.refresh(bom)

    return ProductMaterialSchema(
        id=bom.id,
        product_id=bom.product_id,
        product_name=bom.product.name if bom.product else "未知商品",
        material_id=bom.material_id,
        material_name=bom.material.name if bom.material else "未知物料",
        quantity=float(bom.quantity),
        unit=bom.material.unit if bom.material else "份",
    )


@router.delete("/bom/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bom(db: DbSession, admin: CurrentAdmin, bom_id: str):
    """
    刪除 BOM 對應
    """
    bom = db.query(ProductMaterial).filter(ProductMaterial.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 對應不存在")

    db.delete(bom)
    db.commit()
