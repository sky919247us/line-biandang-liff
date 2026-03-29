"""
管理後台 - 商品 API

提供商品管理功能
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentAdmin
from app.models.product import Product, Category, CustomizationOption


router = APIRouter(prefix="/products", tags=["Admin - Products"])


# ==================== Schemas ====================

class CustomizationOptionSchema(BaseModel):
    """客製化選項 Schema"""
    id: Optional[str] = None
    name: str
    option_type: str = "modifier"
    price_adjustment: float = 0
    is_default: bool = False
    group_id: Optional[str] = None


class ProductSchema(BaseModel):
    """商品 Schema"""
    id: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None
    is_combo: bool = False
    available_periods: Optional[List[str]] = None
    image_url: Optional[str] = None
    daily_limit: int = 0
    today_sold: int = 0
    is_available: bool = True
    is_active: bool = True
    can_order: bool = True
    effective_price: float = 0
    customization_options: List[CustomizationOptionSchema] = []


class ProductCreateRequest(BaseModel):
    """建立商品請求"""
    category_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    daily_limit: int = 0
    is_available: bool = True
    customization_options: List[CustomizationOptionSchema] = []


class ProductUpdateRequest(BaseModel):
    """更新商品請求"""
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sale_price: Optional[float] = None
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None
    is_combo: Optional[bool] = None
    available_periods: Optional[List[str]] = None
    image_url: Optional[str] = None
    daily_limit: Optional[int] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None


class CategorySchema(BaseModel):
    """分類 Schema"""
    id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    product_count: int = 0


class CategoryCreateRequest(BaseModel):
    """建立分類請求"""
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0


# ==================== 工具函式 ====================

def _build_product_schema(product: Product) -> ProductSchema:
    """從 Product model 建立 ProductSchema"""
    options = [
        CustomizationOptionSchema(
            id=opt.id,
            name=opt.name,
            option_type=opt.option_type,
            price_adjustment=float(opt.price_adjustment),
            is_default=opt.is_default,
            group_id=getattr(opt, 'group_id', None),
        )
        for opt in product.customization_options
        if opt.is_active
    ]

    effective_price = float(getattr(product, 'effective_price', product.price))

    return ProductSchema(
        id=product.id,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        name=product.name,
        description=product.description,
        price=float(product.price),
        sale_price=float(product.sale_price) if hasattr(product, 'sale_price') and product.sale_price is not None else None,
        effective_price=effective_price,
        sale_start=getattr(product, 'sale_start', None),
        sale_end=getattr(product, 'sale_end', None),
        is_combo=getattr(product, 'is_combo', False) or False,
        available_periods=getattr(product, 'available_periods', None),
        image_url=product.image_url,
        daily_limit=product.daily_limit,
        today_sold=product.today_sold,
        is_available=product.is_available,
        is_active=product.is_active,
        can_order=product.can_order,
        customization_options=options
    )


# ==================== API 端點 ====================

@router.get("/categories", response_model=List[CategorySchema])
async def get_categories(
    db: DbSession,
    admin: CurrentAdmin  # 需要管理員權限
):
    """
    取得所有分類
    """
    categories = db.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.sort_order, Category.name).all()
    
    result = []
    for cat in categories:
        product_count = db.query(Product).filter(
            Product.category_id == cat.id,
            Product.is_active == True
        ).count()
        
        result.append(CategorySchema(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            image_url=cat.image_url,
            sort_order=cat.sort_order,
            product_count=product_count
        ))
    
    return result


@router.post("/categories", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreateRequest,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    建立新分類
    """
    category = Category(
        name=request.name,
        description=request.description,
        image_url=request.image_url,
        sort_order=request.sort_order,
        is_active=True
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return CategorySchema(
        id=category.id,
        name=category.name,
        description=category.description,
        image_url=category.image_url,
        sort_order=category.sort_order,
        product_count=0
    )


@router.get("", response_model=List[ProductSchema])
async def get_products(
    db: DbSession,
    admin: CurrentAdmin,  # 需要管理員權限
    category_id: Optional[str] = Query(None, description="篩選分類"),
    is_available: Optional[bool] = Query(None, description="篩選上架狀態"),
    search: Optional[str] = Query(None, description="搜尋名稱"),
):
    """
    取得商品列表
    """
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if is_available is not None:
        query = query.filter(Product.is_available == is_available)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    products = query.order_by(Product.sort_order, Product.name).all()

    return [_build_product_schema(p) for p in products]


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(
    product_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    取得單一商品詳情
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    return _build_product_schema(product)


@router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    建立新商品
    """
    product = Product(
        category_id=request.category_id,
        name=request.name,
        description=request.description,
        price=Decimal(str(request.price)),
        image_url=request.image_url,
        daily_limit=request.daily_limit,
        is_available=request.is_available,
        is_active=True,
        today_sold=0
    )
    
    db.add(product)
    db.flush()
    
    # 建立客製化選項
    for opt_data in request.customization_options:
        option = CustomizationOption(
            product_id=product.id,
            name=opt_data.name,
            option_type=opt_data.option_type,
            price_adjustment=Decimal(str(opt_data.price_adjustment)),
            is_default=opt_data.is_default,
            is_active=True
        )
        db.add(option)
    
    db.commit()
    db.refresh(product)

    return _build_product_schema(product)


@router.patch("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    更新商品資訊
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    if request.category_id is not None:
        product.category_id = request.category_id
    if request.name is not None:
        product.name = request.name
    if request.description is not None:
        product.description = request.description
    if request.price is not None:
        product.price = Decimal(str(request.price))
    if request.image_url is not None:
        product.image_url = request.image_url
    if request.daily_limit is not None:
        product.daily_limit = request.daily_limit
    if request.is_available is not None:
        product.is_available = request.is_available
    if request.is_active is not None:
        product.is_active = request.is_active
    if request.sale_price is not None:
        product.sale_price = Decimal(str(request.sale_price)) if request.sale_price else None
    if request.sale_start is not None:
        product.sale_start = request.sale_start
    if request.sale_end is not None:
        product.sale_end = request.sale_end
    if request.is_combo is not None:
        product.is_combo = request.is_combo
    if request.available_periods is not None:
        product.available_periods = request.available_periods

    db.commit()
    db.refresh(product)

    return _build_product_schema(product)


@router.post("/{product_id}/duplicate", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def duplicate_product(
    product_id: str,
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    複製商品

    複製所有欄位和客製化選項，名稱加上「(複製)」
    """
    source = db.query(Product).filter(Product.id == product_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="商品不存在")

    new_product = Product(
        category_id=source.category_id,
        name=f"{source.name}(複製)",
        description=source.description,
        price=source.price,
        image_url=source.image_url,
        daily_limit=source.daily_limit,
        is_available=source.is_available,
        is_active=source.is_active,
        sort_order=source.sort_order,
        today_sold=0,
    )
    # Copy sale / combo fields if they exist on the model
    for attr in ("sale_price", "sale_start", "sale_end", "is_combo", "available_periods"):
        if hasattr(source, attr):
            setattr(new_product, attr, getattr(source, attr))

    db.add(new_product)
    db.flush()

    # 複製客製化選項
    for opt in source.customization_options:
        if not opt.is_active:
            continue
        new_opt = CustomizationOption(
            product_id=new_product.id,
            name=opt.name,
            option_type=opt.option_type,
            price_adjustment=opt.price_adjustment,
            is_default=opt.is_default,
            is_active=True,
            sort_order=opt.sort_order,
        )
        db.add(new_opt)

    db.commit()
    db.refresh(new_product)

    return _build_product_schema(new_product)


@router.patch("/{product_id}/toggle-availability")
async def toggle_product_availability(
    product_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    切換商品上下架狀態
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    product.is_available = not product.is_available
    db.commit()
    
    return {
        "message": "狀態已更新",
        "product_id": product_id,
        "is_available": product.is_available
    }


@router.post("/{product_id}/reset-sold")
async def reset_product_sold(
    product_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    重置今日銷量
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    product.today_sold = 0
    db.commit()
    
    return {"message": "今日銷量已重置", "product_id": product_id, "today_sold": 0}


@router.post("/reset-all-sold")
async def reset_all_products_sold(
    db: DbSession,
    admin: CurrentAdmin
):
    """
    重置所有商品今日銷量
    
    通常每日凌晨執行
    """
    db.query(Product).update({"today_sold": 0})
    db.commit()
    
    return {"message": "所有商品今日銷量已重置"}


@router.get("/export/csv")
async def export_products_csv(
    db: DbSession,
    admin: CurrentAdmin,
):
    """匯出商品列表為 CSV"""
    import csv
    import io
    from starlette.responses import StreamingResponse

    products = db.query(Product).filter(Product.is_active == True).order_by(Product.sort_order, Product.name).all()

    output = io.StringIO()
    # Add BOM for Excel compatibility
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['名稱', '分類', '價格', '促銷價', '每日限量', '今日已售', '上架狀態', '說明'])

    for p in products:
        cat_name = p.category.name if p.category else ''
        writer.writerow([
            p.name,
            cat_name,
            float(p.price),
            float(p.sale_price) if p.sale_price else '',
            p.daily_limit,
            p.today_sold,
            '是' if p.is_available else '否',
            p.description or '',
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=products.csv"}
    )


@router.post("/import/csv")
async def import_products_csv(
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    批量匯入商品 (CSV)

    預期 CSV 格式：名稱, 分類名稱, 價格, 每日限量, 說明
    NOTE: 目前為佔位端點，完整實作需要 UploadFile 支援
    """
    return {"message": "CSV 匯入功能開發中", "status": "not_implemented"}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    刪除商品（軟刪除）
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 軟刪除：設定 is_active = False
    product.is_active = False
    db.commit()
