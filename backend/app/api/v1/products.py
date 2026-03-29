"""
商品 API 路由

提供商品列表、商品詳情和分類等端點
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import func

from app.api.deps import DbSession, OptionalUser
from app.models.product import Product, Category, CustomizationOption
from app.models.order import Order, OrderItem, OrderStatus


def _map_product_response(product: Product) -> "ProductResponse":
    """Map a Product model to ProductResponse"""
    options = [
        CustomizationOptionResponse(
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

    groups = []
    if hasattr(product, 'customization_groups'):
        for group in product.customization_groups:
            if not group.is_active:
                continue
            group_options = [
                CustomizationOptionResponse(
                    id=opt.id,
                    name=opt.name,
                    option_type=opt.option_type,
                    price_adjustment=float(opt.price_adjustment),
                    is_default=opt.is_default,
                    group_id=group.id,
                )
                for opt in group.options
                if opt.is_active
            ]
            groups.append(CustomizationGroupResponse(
                id=group.id,
                name=group.name,
                group_type=group.group_type,
                min_select=group.min_select,
                max_select=group.max_select,
                is_required=group.is_required,
                options=group_options,
            ))

    effective_price = float(getattr(product, 'effective_price', product.price))
    sale_price = float(product.sale_price) if getattr(product, 'sale_price', None) is not None else None
    sale_start = product.sale_start.isoformat() if getattr(product, 'sale_start', None) else None
    sale_end = product.sale_end.isoformat() if getattr(product, 'sale_end', None) else None

    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=float(product.price),
        sale_price=sale_price,
        effective_price=effective_price,
        image_url=product.image_url,
        category_id=product.category_id,
        is_available=product.is_available,
        can_order=product.can_order,
        daily_limit=product.daily_limit,
        today_sold=product.today_sold,
        is_combo=getattr(product, 'is_combo', False),
        available_periods=getattr(product, 'available_periods', None),
        sale_start=sale_start,
        sale_end=sale_end,
        customization_options=options,
        customization_groups=groups,
    )


router = APIRouter(prefix="/products", tags=["商品"])


class CustomizationOptionResponse(BaseModel):
    """客製化選項回應"""
    id: str
    name: str
    option_type: str
    price_adjustment: float
    is_default: bool
    group_id: Optional[str] = None


class CustomizationGroupResponse(BaseModel):
    """客製化群組回應"""
    id: str
    name: str
    group_type: str
    min_select: int
    max_select: int
    is_required: bool
    options: List[CustomizationOptionResponse]


class ProductResponse(BaseModel):
    """商品回應"""
    id: str
    name: str
    description: Optional[str]
    price: float
    sale_price: Optional[float] = None
    effective_price: float
    image_url: Optional[str]
    category_id: Optional[str]
    is_available: bool
    can_order: bool
    daily_limit: int
    today_sold: int
    is_combo: bool = False
    available_periods: Optional[list] = None
    sale_start: Optional[str] = None
    sale_end: Optional[str] = None
    customization_options: List[CustomizationOptionResponse]
    customization_groups: List[CustomizationGroupResponse] = []


class ProductListResponse(BaseModel):
    """商品列表回應"""
    items: List[ProductResponse]
    total: int


class CategoryResponse(BaseModel):
    """分類回應"""
    id: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    product_count: int


class CategoryListResponse(BaseModel):
    """分類列表回應"""
    items: List[CategoryResponse]


@router.get("", response_model=ProductListResponse)
async def get_products(
    db: DbSession,
    category_id: Optional[str] = Query(None, description="分類 ID 過濾"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    available_only: bool = Query(True, description="只顯示可訂購商品"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(20, ge=1, le=100, description="取得筆數")
):
    """
    取得商品列表
    
    支援分類過濾、搜尋、分頁
    
    Args:
        db: 資料庫會話
        category_id: 分類 ID（可選）
        search: 搜尋關鍵字（可選）
        available_only: 是否只顯示可訂購商品
        skip: 分頁偏移量
        limit: 取得數量
        
    Returns:
        ProductListResponse: 商品列表
    """
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    if available_only:
        query = query.filter(Product.is_available == True)
    
    # 總數
    total = query.count()
    
    # 排序和分頁
    products = query.order_by(Product.sort_order, Product.name).offset(skip).limit(limit).all()
    
    items = [_map_product_response(p) for p in products]
    return ProductListResponse(items=items, total=total)


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(db: DbSession):
    """
    取得所有分類
    
    Args:
        db: 資料庫會話
        
    Returns:
        CategoryListResponse: 分類列表
    """
    categories = db.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.sort_order, Category.name).all()
    
    items = []
    for category in categories:
        product_count = db.query(Product).filter(
            Product.category_id == category.id,
            Product.is_active == True
        ).count()
        
        items.append(CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            image_url=category.image_url,
            product_count=product_count
        ))
    
    return CategoryListResponse(items=items)


@router.get("/popular", response_model=ProductListResponse)
async def get_popular_products(
    db: DbSession,
    limit: int = Query(6, ge=1, le=20, description="取得數量")
):
    """取得熱銷商品（依近7天銷量排序）"""
    seven_days_ago = datetime.now() - timedelta(days=7)

    # 查詢近 7 天非取消訂單的商品銷量
    popular_product_ids = (
        db.query(
            OrderItem.product_id,
            func.sum(OrderItem.quantity).label("total_sold")
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.created_at >= seven_days_ago,
            Order.status != OrderStatus.CANCELLED.value
        )
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )

    product_ids = [row.product_id for row in popular_product_ids]

    if not product_ids:
        return ProductListResponse(items=[], total=0)

    products = db.query(Product).filter(
        Product.id.in_(product_ids),
        Product.is_active == True
    ).all()

    # 按銷量順序排列
    product_map = {p.id: p for p in products}
    ordered_products = [product_map[pid] for pid in product_ids if pid in product_map]

    items = [_map_product_response(p) for p in ordered_products]
    return ProductListResponse(items=items, total=len(items))


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: DbSession
):
    """
    取得商品詳情
    
    Args:
        product_id: 商品 ID
        db: 資料庫會話
        
    Returns:
        ProductResponse: 商品詳情
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )

    return _map_product_response(product)
