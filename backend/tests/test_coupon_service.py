"""
優惠券服務單元測試
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.coupon import Coupon, CouponType
from app.services.coupon_service import CouponService


class TestCouponService:
    """優惠券服務測試類別"""
    
    @pytest.mark.unit
    def test_validate_coupon_success(
        self, db_session, test_user, test_coupon
    ):
        """
        測試優惠券驗證成功
        """
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="TEST100",
            user_id=test_user.id,
            order_subtotal=Decimal("300")  # 高於最低消費 200
        )
        
        assert result.is_valid is True
        assert result.discount_amount == Decimal("100")
        assert result.coupon is not None
        assert result.coupon.code == "TEST100"
    
    @pytest.mark.unit
    def test_validate_coupon_not_found(
        self, db_session, test_user
    ):
        """
        測試優惠券不存在
        """
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="NOTEXIST",
            user_id=test_user.id,
            order_subtotal=Decimal("300")
        )
        
        assert result.is_valid is False
        assert "不存在" in result.error_message
    
    @pytest.mark.unit
    def test_validate_coupon_expired(
        self, db_session, test_user, test_coupon
    ):
        """
        測試優惠券已過期
        """
        # 設定優惠券已過期
        test_coupon.valid_until = datetime.now() - timedelta(days=1)
        db_session.commit()
        
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="TEST100",
            user_id=test_user.id,
            order_subtotal=Decimal("300")
        )
        
        assert result.is_valid is False
        assert "過期" in result.error_message
    
    @pytest.mark.unit
    def test_validate_coupon_not_started(
        self, db_session, test_user, test_coupon
    ):
        """
        測試優惠券尚未生效
        """
        # 設定優惠券尚未開始
        test_coupon.valid_from = datetime.now() + timedelta(days=7)
        db_session.commit()
        
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="TEST100",
            user_id=test_user.id,
            order_subtotal=Decimal("300")
        )
        
        assert result.is_valid is False
        assert "尚未生效" in result.error_message
    
    @pytest.mark.unit
    def test_validate_coupon_min_amount_not_met(
        self, db_session, test_user, test_coupon
    ):
        """
        測試未達最低消費金額
        """
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="TEST100",
            user_id=test_user.id,
            order_subtotal=Decimal("100")  # 低於最低消費 200
        )
        
        assert result.is_valid is False
        assert "滿" in result.error_message
    
    @pytest.mark.unit
    def test_validate_coupon_usage_limit_reached(
        self, db_session, test_user, test_coupon
    ):
        """
        測試優惠券已達使用上限
        """
        # 設定優惠券已用完
        test_coupon.used_count = test_coupon.usage_limit
        db_session.commit()
        
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="TEST100",
            user_id=test_user.id,
            order_subtotal=Decimal("300")
        )
        
        assert result.is_valid is False
        assert "使用上限" in result.error_message
    
    @pytest.mark.unit
    def test_validate_coupon_inactive(
        self, db_session, test_user, test_coupon
    ):
        """
        測試優惠券已停用
        """
        test_coupon.is_active = False
        db_session.commit()
        
        service = CouponService(db_session)
        
        result = service.validate_coupon(
            code="TEST100",
            user_id=test_user.id,
            order_subtotal=Decimal("300")
        )
        
        assert result.is_valid is False
        assert "停用" in result.error_message
    
    @pytest.mark.unit
    def test_percentage_coupon(self, db_session, test_user):
        """
        測試百分比優惠券
        """
        # 建立 10% 折扣優惠券
        coupon = Coupon(
            code="PERCENT10",
            name="九折優惠",
            coupon_type=CouponType.PERCENTAGE.value,
            discount_value=Decimal("10"),  # 10%
            min_order_amount=Decimal("0"),
            max_discount_amount=Decimal("50"),  # 最高折 50
            usage_limit=0,
            per_user_limit=0,
            valid_from=datetime.now() - timedelta(days=1),
            valid_until=datetime.now() + timedelta(days=30),
            is_active=True
        )
        db_session.add(coupon)
        db_session.commit()
        
        service = CouponService(db_session)
        
        # 訂單 300 元，10% = 30 元
        result = service.validate_coupon(
            code="PERCENT10",
            user_id=test_user.id,
            order_subtotal=Decimal("300")
        )
        
        assert result.is_valid is True
        assert result.discount_amount == Decimal("30.00")
    
    @pytest.mark.unit
    def test_percentage_coupon_max_discount(self, db_session, test_user):
        """
        測試百分比優惠券最高折扣上限
        """
        # 建立 10% 折扣優惠券，最高折 50
        coupon = Coupon(
            code="PERCENT10MAX",
            name="九折優惠",
            coupon_type=CouponType.PERCENTAGE.value,
            discount_value=Decimal("10"),
            min_order_amount=Decimal("0"),
            max_discount_amount=Decimal("50"),
            usage_limit=0,
            per_user_limit=0,
            valid_from=datetime.now() - timedelta(days=1),
            valid_until=datetime.now() + timedelta(days=30),
            is_active=True
        )
        db_session.add(coupon)
        db_session.commit()
        
        service = CouponService(db_session)
        
        # 訂單 1000 元，10% = 100 元，但最高折 50
        result = service.validate_coupon(
            code="PERCENT10MAX",
            user_id=test_user.id,
            order_subtotal=Decimal("1000")
        )
        
        assert result.is_valid is True
        assert result.discount_amount == Decimal("50")  # 受最高折扣限制
    
    @pytest.mark.unit
    def test_free_delivery_coupon(self, db_session, test_user):
        """
        測試免運費優惠券
        """
        coupon = Coupon(
            code="FREEDELIVERY",
            name="免運費",
            coupon_type=CouponType.FREE_DELIVERY.value,
            discount_value=Decimal("0"),
            min_order_amount=Decimal("200"),
            usage_limit=0,
            per_user_limit=0,
            valid_from=datetime.now() - timedelta(days=1),
            valid_until=datetime.now() + timedelta(days=30),
            is_active=True
        )
        db_session.add(coupon)
        db_session.commit()
        
        service = CouponService(db_session)
        
        # 外送訂單
        result = service.validate_coupon(
            code="FREEDELIVERY",
            user_id=test_user.id,
            order_subtotal=Decimal("300"),
            order_type="delivery"
        )
        
        assert result.is_valid is True
        assert result.is_free_delivery is True
        assert result.discount_amount == Decimal("0")
    
    @pytest.mark.unit
    def test_free_delivery_coupon_pickup_denied(self, db_session, test_user):
        """
        測試免運費優惠券不適用自取訂單
        """
        coupon = Coupon(
            code="FREEDELIVERY2",
            name="免運費",
            coupon_type=CouponType.FREE_DELIVERY.value,
            discount_value=Decimal("0"),
            min_order_amount=Decimal("0"),
            usage_limit=0,
            per_user_limit=0,
            valid_from=datetime.now() - timedelta(days=1),
            valid_until=datetime.now() + timedelta(days=30),
            is_active=True
        )
        db_session.add(coupon)
        db_session.commit()
        
        service = CouponService(db_session)
        
        # 自取訂單
        result = service.validate_coupon(
            code="FREEDELIVERY2",
            user_id=test_user.id,
            order_subtotal=Decimal("300"),
            order_type="pickup"
        )
        
        assert result.is_valid is False
        assert "外送" in result.error_message
    
    @pytest.mark.unit
    def test_apply_and_revoke_coupon(
        self, db_session, test_user, test_coupon, test_order
    ):
        """
        測試應用和撤銷優惠券
        """
        service = CouponService(db_session)
        
        # 應用優惠券
        initial_used_count = test_coupon.used_count
        
        result = service.apply_coupon(
            coupon_id=test_coupon.id,
            user_id=test_user.id,
            order_id=test_order.id,
            discount_amount=Decimal("100")
        )
        
        assert result is True
        
        db_session.refresh(test_coupon)
        assert test_coupon.used_count == initial_used_count + 1
        
        # 撤銷優惠券
        result = service.revoke_coupon_usage(test_order.id)
        
        assert result is True
        
        db_session.refresh(test_coupon)
        assert test_coupon.used_count == initial_used_count
