"""
訂單 API 整合測試
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product


class TestOrdersAPI:
    """訂單 API 測試類別"""
    
    @pytest.mark.integration
    def test_get_order_availability(self, client):
        """
        測試取得訂單可用性
        """
        response = client.get("/api/v1/orders/availability")
        
        assert response.status_code == 200
        data = response.json()
        assert "can_order" in data
        assert "today_count" in data
        assert "daily_limit" in data
        assert "remaining" in data
        assert isinstance(data["can_order"], bool)
    
    @pytest.mark.integration
    def test_get_order_availability_when_limit_reached(
        self, client, db_session, test_user, test_product
    ):
        """
        測試當訂單上限達到時的可用性
        """
        # 建立多個訂單達到上限
        from app.core.config import settings
        
        # 模擬今日訂單數量（明確設定 created_at 為本地時間以匹配查詢邏輯）
        now = datetime.now()
        for i in range(settings.daily_order_limit):
            order = Order(
                user_id=test_user.id,
                order_number=f"TEST-{now.strftime('%Y%m%d')}-{i:03d}",
                order_type="pickup",
                status=OrderStatus.PENDING.value,
                subtotal=Decimal("100"),
                delivery_fee=Decimal("0"),
                discount=Decimal("0"),
                total=Decimal("100"),
                contact_name="測試",
                contact_phone="0912345678",
                created_at=now,
            )
            db_session.add(order)
        db_session.commit()
        
        response = client.get("/api/v1/orders/availability")
        
        assert response.status_code == 200
        data = response.json()
        assert data["can_order"] is False
        assert data["remaining"] == 0


class TestOrderCreation:
    """訂單建立測試類別"""
    
    @pytest.mark.integration
    def test_create_order_requires_auth(self, client):
        """
        測試建立訂單需要認證
        """
        response = client.post(
            "/api/v1/orders",
            json={
                "order_type": "pickup",
                "items": [{"product_id": "test", "quantity": 1}]
            }
        )
        
        # 應該返回未認證錯誤
        assert response.status_code in [401, 403]
    
    @pytest.mark.integration
    def test_create_order_validation(self, client):
        """
        測試訂單建立驗證
        """
        # 空訂單項目
        response = client.post(
            "/api/v1/orders",
            json={
                "order_type": "pickup",
                "items": []
            }
        )
        
        # 應該返回驗證錯誤
        assert response.status_code in [401, 403, 422]


class TestOrderStatus:
    """訂單狀態測試類別"""
    
    @pytest.mark.integration
    def test_get_order_status_not_found(self, client):
        """
        測試查詢不存在的訂單
        """
        response = client.get("/api/v1/orders/non-existent-order-id")
        
        assert response.status_code in [401, 404]
    
    @pytest.mark.integration
    def test_order_status_transitions(self, db_session, test_order):
        """
        測試訂單狀態轉換
        """
        # 初始狀態
        assert test_order.status == OrderStatus.PENDING.value
        
        # 確認訂單
        test_order.status = OrderStatus.CONFIRMED.value
        db_session.commit()
        assert test_order.status == OrderStatus.CONFIRMED.value
        
        # 製作中
        test_order.status = OrderStatus.PREPARING.value
        db_session.commit()
        assert test_order.status == OrderStatus.PREPARING.value
        
        # 可取餐
        test_order.status = OrderStatus.READY.value
        db_session.commit()
        assert test_order.status == OrderStatus.READY.value
        
        # 已完成
        test_order.status = OrderStatus.COMPLETED.value
        db_session.commit()
        assert test_order.status == OrderStatus.COMPLETED.value


class TestOrderCancel:
    """訂單取消測試類別"""
    
    @pytest.mark.integration
    def test_cancel_order_restores_stock(
        self, db_session, test_order, test_product, test_material, test_bom
    ):
        """
        測試取消訂單回補庫存
        """
        from app.services.inventory_service import InventoryService
        
        # 記錄初始庫存
        initial_stock = float(test_material.current_stock)
        
        # 模擬訂單已扣減庫存
        service = InventoryService(db_session)
        items = [{"product_id": test_product.id, "quantity": 1}]
        service.deduct_stock_for_order(items)
        
        db_session.refresh(test_material)
        after_deduct = float(test_material.current_stock)
        assert after_deduct < initial_stock
        
        # 取消訂單並回補
        test_order.status = OrderStatus.CANCELLED.value
        service.restore_stock_for_order(items)
        
        db_session.refresh(test_material)
        after_restore = float(test_material.current_stock)
        assert after_restore == initial_stock
