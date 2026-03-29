"""
優惠券 API

提供優惠券驗證、查詢等功能
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUser
from app.models.coupon import Coupon
from app.services.coupon_service import CouponService


router = APIRouter(prefix="/coupons", tags=["Coupons"])


# ==================== Schemas ====================

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
    valid_until: datetime
    remaining_usage: Optional[int] = None
    user_can_use: bool = True


class ValidateCouponRequest(BaseModel):
    """驗證優惠券請求"""
    code: str
    order_subtotal: float
    order_type: str = "pickup"  # pickup or delivery


class ValidateCouponResponse(BaseModel):
    """驗證優惠券回應"""
    is_valid: bool
    discount_amount: float = 0
    is_free_delivery: bool = False
    error_message: Optional[str] = None
    coupon: Optional[CouponSchema] = None


class UserCouponsResponse(BaseModel):
    """使用者優惠券列表回應"""
    coupons: List[CouponSchema]
    total: int


# ==================== API 端點 ====================

@router.get("/my", response_model=UserCouponsResponse)
async def get_my_coupons(
    db: DbSession,
    current_user: CurrentUser
):
    """
    取得我可用的優惠券
    """
    coupon_service = CouponService(db)
    coupons_data = coupon_service.get_user_coupons(current_user.id)
    
    coupons = [
        CouponSchema(
            id=c["id"],
            code=c["code"],
            name=c["name"],
            description=c["description"],
            coupon_type=c["coupon_type"],
            discount_value=c["discount_value"],
            min_order_amount=c["min_order_amount"],
            max_discount_amount=c["max_discount_amount"],
            valid_until=datetime.fromisoformat(c["valid_until"]),
            remaining_usage=c["remaining_usage"],
            user_can_use=c["user_can_use"]
        )
        for c in coupons_data
        if c["user_can_use"]
    ]
    
    return UserCouponsResponse(
        coupons=coupons,
        total=len(coupons)
    )


@router.post("/validate", response_model=ValidateCouponResponse)
async def validate_coupon(
    request: ValidateCouponRequest,
    db: DbSession,
    current_user: CurrentUser
):
    """
    驗證優惠券
    
    檢查優惠券是否可用，並計算折扣金額
    """
    coupon_service = CouponService(db)
    
    result = coupon_service.validate_coupon(
        code=request.code,
        user_id=current_user.id,
        order_subtotal=Decimal(str(request.order_subtotal)),
        order_type=request.order_type
    )
    
    if not result.is_valid:
        return ValidateCouponResponse(
            is_valid=False,
            error_message=result.error_message
        )
    
    coupon = result.coupon
    
    return ValidateCouponResponse(
        is_valid=True,
        discount_amount=float(result.discount_amount),
        is_free_delivery=result.is_free_delivery,
        coupon=CouponSchema(
            id=coupon.id,
            code=coupon.code,
            name=coupon.name,
            description=coupon.description,
            coupon_type=coupon.coupon_type,
            discount_value=float(coupon.discount_value),
            min_order_amount=float(coupon.min_order_amount),
            max_discount_amount=float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
            valid_until=coupon.valid_until,
            remaining_usage=coupon.remaining_usage,
            user_can_use=True
        )
    )


@router.get("/{code}")
async def get_coupon_info(
    code: str,
    db: DbSession
):
    """
    取得優惠券基本資訊（公開）
    
    不需要登入即可查詢
    """
    coupon = db.query(Coupon).filter(
        Coupon.code == code.upper(),
        Coupon.is_active == True
    ).first()
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="優惠券不存在或已停用"
        )
    
    now = datetime.now()
    is_expired = now > coupon.valid_until
    is_not_started = now < coupon.valid_from
    is_exhausted = coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit
    
    return {
        "code": coupon.code,
        "name": coupon.name,
        "description": coupon.description,
        "coupon_type": coupon.coupon_type,
        "discount_value": float(coupon.discount_value),
        "min_order_amount": float(coupon.min_order_amount),
        "valid_from": coupon.valid_from.isoformat(),
        "valid_until": coupon.valid_until.isoformat(),
        "is_available": coupon.is_valid,
        "is_expired": is_expired,
        "is_not_started": is_not_started,
        "is_exhausted": is_exhausted
    }
