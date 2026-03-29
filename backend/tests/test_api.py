"""
API 整合測試
"""
import pytest
from fastapi.testclient import TestClient


class TestProductsAPI:
    """商品 API 測試類別"""
    
    @pytest.mark.integration
    def test_get_products(self, client, db_session, test_product, test_category):
        """
        測試取得商品列表
        """
        response = client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
    
    @pytest.mark.integration
    def test_get_product_by_id(self, client, db_session, test_product):
        """
        測試取得單一商品
        """
        response = client.get(f"/api/v1/products/{test_product.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name
    
    @pytest.mark.integration
    def test_get_product_not_found(self, client):
        """
        測試商品不存在
        """
        response = client.get("/api/v1/products/non-existent-id")
        
        assert response.status_code == 404
    
    @pytest.mark.integration
    def test_get_categories(self, client, db_session, test_category):
        """
        測試取得分類列表
        """
        response = client.get("/api/v1/products/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestOrdersAPI:
    """訂單 API 測試類別"""
    
    @pytest.mark.integration
    def test_order_availability(self, client):
        """
        測試訂單可用性
        """
        response = client.get("/api/v1/orders/availability")
        
        assert response.status_code == 200
        data = response.json()
        assert "can_order" in data
        assert "today_count" in data
        assert "daily_limit" in data


class TestDeliveryAPI:
    """配送 API 測試類別"""
    
    @pytest.mark.integration
    def test_get_delivery_info(self, client):
        """
        測試取得配送資訊
        """
        response = client.get("/api/v1/delivery/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "delivery_enabled" in data
        assert "max_distance_km" in data
    
    @pytest.mark.integration
    def test_calculate_delivery_fee(self, client):
        """
        測試計算運費
        """
        response = client.post(
            "/api/v1/delivery/calculate",
            json={
                "address": "台中市中區興中街20號",
                "order_amount": 300
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "final_delivery_fee" in data
        assert "is_valid" in data


class TestHealthAPI:
    """健康檢查 API 測試"""
    
    @pytest.mark.integration
    def test_root(self, client):
        """
        測試根路徑
        """
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
    
    @pytest.mark.integration
    def test_health(self, client):
        """
        測試健康檢查
        """
        response = client.get("/health")
        
        assert response.status_code == 200
