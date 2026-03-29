"""
管理後台 - 優惠券 API

提供優惠券管理功能
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentAdmin
from app.models.coupon import Coupon, CouponUsage, CouponType


router = APIRouter(prefix="/coupons", tags=["Admin - Coupons"])


# ==================== Schemas ====================

class CouponCreateRequest(BaseModel):
    """建立優惠券請求"""
    code: str
    name: str
    description: Optional[str] = None
    coupon_type: str = "fixed"
    discount_value: float
    min_order_amount: float = 0
    max_discount_amount: Optional[float] = None
    usage_limit: int = 0
    per_user_limit: int = 1
    valid_from: datetime
    valid_until: datetime


class CouponUpdateRequest(BaseModel):
    """更新優惠券請求"""
    name: Optional[str] = None
    description: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponSchema(BaseModel):
    """優惠券 Schema"""
    id: str
    code: str
    name: str
    description: Optional[str] = None
    coupon_type: str
    discount_value: float
    min_order_amount: float
    max_discount_amount: Optional[float] = None
    usage_limit: int
    per_user_limit: int
    used_count: int
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    is_valid: bool
    remaining_usage: Optional[int] = None
    created_at: datetime


class CouponUsageSchema(BaseModel):
    """優惠券使用記錄 Schema"""
    id: str
    coupon_code: str
    user_display_name: Optional[str] = None
    order_number: str
    discount_amount: float
    used_at: datetime


class CouponListResponse(BaseModel):
    """優惠券列表回應"""
    coupons: List[CouponSchema]
    total: int
    page: int
    page_size: int


# ==================== 輔助函式 ====================

COUPON_TYPE_LABELS = {
    "fixed": "固定金額",
    "percentage": "百分比",
    "free_delivery": "免運費"
}


# ==================== API 端點 ====================

@router.get("/types")
async def get_coupon_types(admin: CurrentAdmin):
    """
    取得優惠券類型選項
    """
    return [
        {"value": t.value, "label": COUPON_TYPE_LABELS.get(t.value, t.value)}
        for t in CouponType
    ]


@router.get("", response_model=CouponListResponse)
async def get_coupons(
    db: DbSession,
    admin: CurrentAdmin,
    is_active: Optional[bool] = Query(None, description="篩選啟用狀態"),
    search: Optional[str] = Query(None, description="搜尋代碼或名稱"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    取得優惠券列表
    """
    query = db.query(Coupon)
    
    if is_active is not None:
        query = query.filter(Coupon.is_active == is_active)
    
    if search:
        query = query.filter(
            (Coupon.code.ilike(f"%{search}%")) |
            (Coupon.name.ilike(f"%{search}%"))
        )
    
    total = query.count()
    coupons = query.order_by(Coupon.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    result = [
        CouponSchema(
            id=c.id,
            code=c.code,
            name=c.name,
            description=c.description,
            coupon_type=c.coupon_type,
            discount_value=float(c.discount_value),
            min_order_amount=float(c.min_order_amount),
            max_discount_amount=float(c.max_discount_amount) if c.max_discount_amount else None,
            usage_limit=c.usage_limit,
            per_user_limit=c.per_user_limit,
            used_count=c.used_count,
            valid_from=c.valid_from,
            valid_until=c.valid_until,
            is_active=c.is_active,
            is_valid=c.is_valid,
            remaining_usage=c.remaining_usage,
            created_at=c.created_at
        )
        for c in coupons
    ]
    
    return CouponListResponse(
        coupons=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{coupon_id}", response_model=CouponSchema)
async def get_coupon(
    coupon_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    取得單一優惠券詳情
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="優惠券不存在")
    
    return CouponSchema(
        id=coupon.id,
        code=coupon.code,
        name=coupon.name,
        description=coupon.description,
        coupon_type=coupon.coupon_type,
        discount_value=float(coupon.discount_value),
        min_order_amount=float(coupon.min_order_amount),
        max_discount_amount=float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
        usage_limit=coupon.usage_limit,
        per_user_limit=coupon.per_user_limit,
        used_count=coupon.used_count,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        is_active=coupon.is_active,
        is_valid=coupon.is_valid,
        remaining_usage=coupon.remaining_usage,
        created_at=coupon.created_at
    )


@router.post("", response_model=CouponSchema, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    request: CouponCreateRequest,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    建立新優惠券
    """
    # 驗證優惠券類型
    valid_types = [t.value for t in CouponType]
    if request.coupon_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的優惠券類型，有效值：{', '.join(valid_types)}"
        )
    
    # 檢查代碼是否重複
    code_upper = request.code.upper()
    existing = db.query(Coupon).filter(Coupon.code == code_upper).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="優惠券代碼已存在"
        )
    
    # 驗證日期
    if request.valid_until <= request.valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="結束時間必須大於開始時間"
        )
    
    coupon = Coupon(
        code=code_upper,
        name=request.name,
        description=request.description,
        coupon_type=request.coupon_type,
        discount_value=Decimal(str(request.discount_value)),
        min_order_amount=Decimal(str(request.min_order_amount)),
        max_discount_amount=Decimal(str(request.max_discount_amount)) if request.max_discount_amount else None,
        usage_limit=request.usage_limit,
        per_user_limit=request.per_user_limit,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        is_active=True,
        used_count=0
    )
    
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    
    return CouponSchema(
        id=coupon.id,
        code=coupon.code,
        name=coupon.name,
        description=coupon.description,
        coupon_type=coupon.coupon_type,
        discount_value=float(coupon.discount_value),
        min_order_amount=float(coupon.min_order_amount),
        max_discount_amount=float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
        usage_limit=coupon.usage_limit,
        per_user_limit=coupon.per_user_limit,
        used_count=coupon.used_count,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        is_active=coupon.is_active,
        is_valid=coupon.is_valid,
        remaining_usage=coupon.remaining_usage,
        created_at=coupon.created_at
    )


@router.patch("/{coupon_id}", response_model=CouponSchema)
async def update_coupon(
    coupon_id: str,
    request: CouponUpdateRequest,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    更新優惠券
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="優惠券不存在")
    
    if request.name is not None:
        coupon.name = request.name
    if request.description is not None:
        coupon.description = request.description
    if request.discount_value is not None:
        coupon.discount_value = Decimal(str(request.discount_value))
    if request.min_order_amount is not None:
        coupon.min_order_amount = Decimal(str(request.min_order_amount))
    if request.max_discount_amount is not None:
        coupon.max_discount_amount = Decimal(str(request.max_discount_amount))
    if request.usage_limit is not None:
        coupon.usage_limit = request.usage_limit
    if request.per_user_limit is not None:
        coupon.per_user_limit = request.per_user_limit
    if request.valid_from is not None:
        coupon.valid_from = request.valid_from
    if request.valid_until is not None:
        coupon.valid_until = request.valid_until
    if request.is_active is not None:
        coupon.is_active = request.is_active
    
    db.commit()
    db.refresh(coupon)
    
    return CouponSchema(
        id=coupon.id,
        code=coupon.code,
        name=coupon.name,
        description=coupon.description,
        coupon_type=coupon.coupon_type,
        discount_value=float(coupon.discount_value),
        min_order_amount=float(coupon.min_order_amount),
        max_discount_amount=float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
        usage_limit=coupon.usage_limit,
        per_user_limit=coupon.per_user_limit,
        used_count=coupon.used_count,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        is_active=coupon.is_active,
        is_valid=coupon.is_valid,
        remaining_usage=coupon.remaining_usage,
        created_at=coupon.created_at
    )


@router.patch("/{coupon_id}/toggle")
async def toggle_coupon(
    coupon_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    切換優惠券啟用狀態
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="優惠券不存在")
    
    coupon.is_active = not coupon.is_active
    db.commit()
    
    return {
        "message": f"優惠券已{'啟用' if coupon.is_active else '停用'}",
        "coupon_id": coupon_id,
        "is_active": coupon.is_active
    }


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(
    coupon_id: str,
    db: DbSession,
    admin: CurrentAdmin
):
    """
    刪除優惠券
    
    若有使用記錄則無法刪除
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="優惠券不存在")
    
    if coupon.used_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此優惠券已有使用記錄，無法刪除"
        )
    
    db.delete(coupon)
    db.commit()


@router.get("/{coupon_id}/usages", response_model=List[CouponUsageSchema])
async def get_coupon_usages(
    coupon_id: str,
    db: DbSession,
    admin: CurrentAdmin,
    limit: int = Query(50, ge=1, le=200),
):
    """
    取得優惠券使用記錄
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="優惠券不存在")
    
    usages = db.query(CouponUsage).filter(
        CouponUsage.coupon_id == coupon_id
    ).order_by(CouponUsage.used_at.desc()).limit(limit).all()
    
    return [
        CouponUsageSchema(
            id=u.id,
            coupon_code=coupon.code,
            user_display_name=u.user.display_name if u.user else None,
            order_number=u.order.order_number if u.order else "N/A",
            discount_amount=float(u.discount_amount),
            used_at=u.used_at
        )
        for u in usages
    ]
