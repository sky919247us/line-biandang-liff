"""
優惠券服務

處理優惠券驗證、折扣計算和使用記錄
"""
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponUsage, CouponType


logger = logging.getLogger(__name__)


@dataclass
class CouponValidationResult:
    """優惠券驗證結果"""
    is_valid: bool
    coupon: Optional[Coupon] = None
    discount_amount: Decimal = Decimal("0")
    error_message: Optional[str] = None
    is_free_delivery: bool = False


class CouponService:
    """
    優惠券服務
    
    負責處理：
    1. 優惠券代碼驗證
    2. 折扣金額計算
    3. 使用記錄管理
    4. 使用次數限制檢查
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_coupon(
        self,
        code: str,
        user_id: str,
        order_subtotal: Decimal,
        order_type: str = "pickup"
    ) -> CouponValidationResult:
        """
        驗證優惠券
        
        Args:
            code: 優惠券代碼
            user_id: 使用者 ID
            order_subtotal: 訂單小計
            order_type: 訂單類型 (pickup/delivery)
            
        Returns:
            CouponValidationResult: 驗證結果
        """
        # 查詢優惠券
        coupon = self.db.query(Coupon).filter(
            Coupon.code == code.upper()
        ).first()
        
        if not coupon:
            return CouponValidationResult(
                is_valid=False,
                error_message="優惠券代碼不存在"
            )
        
        # 檢查是否啟用
        if not coupon.is_active:
            return CouponValidationResult(
                is_valid=False,
                error_message="此優惠券已停用"
            )
        
        # 檢查有效期
        now = datetime.now()
        if now < coupon.valid_from:
            return CouponValidationResult(
                is_valid=False,
                error_message=f"優惠券尚未生效，生效時間：{coupon.valid_from.strftime('%Y-%m-%d')}"
            )
        
        if now > coupon.valid_until:
            return CouponValidationResult(
                is_valid=False,
                error_message="優惠券已過期"
            )
        
        # 檢查總使用次數
        if coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit:
            return CouponValidationResult(
                is_valid=False,
                error_message="優惠券已達使用上限"
            )
        
        # 檢查使用者使用次數
        if coupon.per_user_limit > 0:
            user_usage_count = self.db.query(CouponUsage).filter(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id
            ).count()
            
            if user_usage_count >= coupon.per_user_limit:
                return CouponValidationResult(
                    is_valid=False,
                    error_message=f"您已使用此優惠券 {user_usage_count} 次，已達個人使用上限"
                )
        
        # 檢查最低消費
        if order_subtotal < coupon.min_order_amount:
            return CouponValidationResult(
                is_valid=False,
                error_message=f"訂單金額需滿 ${coupon.min_order_amount} 才能使用此優惠券"
            )
        
        # 免運費優惠券檢查
        if coupon.coupon_type == CouponType.FREE_DELIVERY.value:
            if order_type != "delivery":
                return CouponValidationResult(
                    is_valid=False,
                    error_message="此優惠券僅限外送訂單使用"
                )
            
            return CouponValidationResult(
                is_valid=True,
                coupon=coupon,
                discount_amount=Decimal("0"),
                is_free_delivery=True
            )
        
        # 計算折扣金額
        discount_amount = coupon.calculate_discount(order_subtotal)
        
        return CouponValidationResult(
            is_valid=True,
            coupon=coupon,
            discount_amount=discount_amount
        )
    
    def apply_coupon(
        self,
        coupon_id: str,
        user_id: str,
        order_id: str,
        discount_amount: Decimal
    ) -> bool:
        """
        應用優惠券（記錄使用）
        
        Args:
            coupon_id: 優惠券 ID
            user_id: 使用者 ID
            order_id: 訂單 ID
            discount_amount: 折扣金額
            
        Returns:
            是否成功
        """
        coupon = self.db.query(Coupon).filter(
            Coupon.id == coupon_id
        ).with_for_update().first()
        
        if not coupon:
            logger.error(f"優惠券 {coupon_id} 不存在")
            return False
        
        # 建立使用記錄
        usage = CouponUsage(
            coupon_id=coupon_id,
            user_id=user_id,
            order_id=order_id,
            discount_amount=discount_amount
        )
        
        self.db.add(usage)

        # 更新使用次數
        coupon.used_count += 1
        self.db.flush()

        logger.info(
            f"優惠券 {coupon.code} 已被使用，"
            f"使用者: {user_id}, 訂單: {order_id}, 折扣: ${discount_amount}"
        )

        return True
    
    def revoke_coupon_usage(
        self,
        order_id: str
    ) -> bool:
        """
        撤銷優惠券使用（訂單取消時）
        
        Args:
            order_id: 訂單 ID
            
        Returns:
            是否成功
        """
        usage = self.db.query(CouponUsage).filter(
            CouponUsage.order_id == order_id
        ).first()
        
        if not usage:
            return True  # 沒有使用優惠券
        
        # 減少優惠券使用次數
        coupon = self.db.query(Coupon).filter(
            Coupon.id == usage.coupon_id
        ).with_for_update().first()
        
        if coupon and coupon.used_count > 0:
            coupon.used_count -= 1

        # 刪除使用記錄
        self.db.delete(usage)
        self.db.flush()

        logger.info(f"訂單 {order_id} 的優惠券使用已撤銷")

        return True
    
    def get_user_coupons(
        self,
        user_id: str,
        include_used: bool = False
    ) -> list:
        """
        取得使用者可用的優惠券
        
        Args:
            user_id: 使用者 ID
            include_used: 是否包含已用完的
            
        Returns:
            優惠券清單
        """
        now = datetime.now()
        
        query = self.db.query(Coupon).filter(
            Coupon.is_active == True,
            Coupon.valid_from <= now,
            Coupon.valid_until >= now
        )
        
        coupons = query.all()
        
        result = []
        for coupon in coupons:
            # 檢查總使用次數
            if coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit:
                if not include_used:
                    continue
            
            # 檢查個人使用次數
            user_usage_count = self.db.query(CouponUsage).filter(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id
            ).count()
            
            if coupon.per_user_limit > 0 and user_usage_count >= coupon.per_user_limit:
                if not include_used:
                    continue
            
            result.append({
                "id": coupon.id,
                "code": coupon.code,
                "name": coupon.name,
                "description": coupon.description,
                "coupon_type": coupon.coupon_type,
                "discount_value": float(coupon.discount_value),
                "min_order_amount": float(coupon.min_order_amount),
                "max_discount_amount": float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
                "valid_until": coupon.valid_until.isoformat(),
                "remaining_usage": coupon.remaining_usage,
                "user_usage_count": user_usage_count,
                "user_can_use": user_usage_count < coupon.per_user_limit if coupon.per_user_limit > 0 else True
            })
        
        return result


def get_coupon_service(db: Session) -> CouponService:
    """取得優惠券服務實例"""
    return CouponService(db)
