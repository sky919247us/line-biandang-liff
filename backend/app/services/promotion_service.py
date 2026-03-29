"""
促銷服務

處理自動套用優惠券邏輯，包含滿額折扣和首購折扣
"""
import logging
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponUsage, CouponType
from app.models.order import Order, OrderStatus


logger = logging.getLogger(__name__)


class PromotionService:
    """
    促銷服務

    負責處理：
    1. 查詢可自動套用的優惠券
    2. 首購資格檢查
    3. 選擇最佳優惠券
    """

    def __init__(self, db: Session):
        self.db = db

    def _is_first_purchase(self, user_id: str) -> bool:
        """
        檢查使用者是否為首次購買

        Args:
            user_id: 使用者 ID

        Returns:
            是否為首次購買（無已完成訂單）
        """
        completed_order_count = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status != OrderStatus.CANCELLED.value
        ).count()

        return completed_order_count == 0

    def get_auto_apply_coupons(
        self,
        user_id: str,
        order_total: Decimal
    ) -> List[Coupon]:
        """
        取得可自動套用的優惠券清單

        Args:
            user_id: 使用者 ID
            order_total: 訂單金額

        Returns:
            符合條件的優惠券清單，依折扣金額由大到小排序
        """
        now = datetime.now()

        # 查詢所有啟用中且在有效期內的自動套用優惠券
        coupons = self.db.query(Coupon).filter(
            Coupon.is_auto_apply == True,
            Coupon.is_active == True,
            Coupon.valid_from <= now,
            Coupon.valid_until >= now
        ).all()

        applicable = []
        is_first = None  # 延遲查詢首購狀態

        for coupon in coupons:
            # 檢查總使用次數限制
            if coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit:
                continue

            # 檢查個人使用次數限制
            if coupon.per_user_limit > 0:
                user_usage_count = self.db.query(CouponUsage).filter(
                    CouponUsage.coupon_id == coupon.id,
                    CouponUsage.user_id == user_id
                ).count()
                if user_usage_count >= coupon.per_user_limit:
                    continue

            # 檢查首購限制
            if coupon.first_purchase_only:
                if is_first is None:
                    is_first = self._is_first_purchase(user_id)
                if not is_first:
                    continue

            # 檢查最低消費門檻
            if order_total < coupon.min_order_amount:
                continue

            # 計算折扣金額並確認大於 0
            discount = coupon.calculate_discount(order_total)
            if discount > Decimal("0"):
                applicable.append((coupon, discount))

        # 依折扣金額由大到小排序
        applicable.sort(key=lambda x: x[1], reverse=True)

        return [item[0] for item in applicable]

    def get_best_auto_coupon(
        self,
        user_id: str,
        order_total: Decimal
    ) -> Optional[Coupon]:
        """
        取得最佳的自動套用優惠券

        Args:
            user_id: 使用者 ID
            order_total: 訂單金額

        Returns:
            折扣金額最高的優惠券，或 None
        """
        coupons = self.get_auto_apply_coupons(user_id, order_total)

        if not coupons:
            return None

        best = coupons[0]
        logger.info(
            f"自動套用優惠券: {best.code} (類型: {best.coupon_type}), "
            f"使用者: {user_id}, 訂單金額: ${order_total}"
        )
        return best
