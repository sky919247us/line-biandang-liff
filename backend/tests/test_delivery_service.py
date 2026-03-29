"""
配送服務單元測試
"""
import pytest

from app.services.delivery_service import DeliveryService


class TestDeliveryService:
    """配送服務測試類別"""

    @pytest.mark.unit
    def test_haversine_distance(self):
        """測試 Haversine 距離計算"""
        service = DeliveryService()

        # 台北 101 到台北車站（直線約 5 公里）
        distance = service.calculate_distance_haversine(
            25.0339, 121.5645,  # 台北 101
            25.0478, 121.5170,  # 台北車站
        )

        assert 4.5 < distance < 5.5

    @pytest.mark.unit
    def test_haversine_same_point(self):
        """同一點距離為 0"""
        service = DeliveryService()
        distance = service.calculate_distance_haversine(
            24.1378, 120.6828,
            24.1378, 120.6828,
        )
        assert distance == 0.0

    @pytest.mark.unit
    def test_calculate_delivery_fee_within_free_tier(self):
        """2km 以內免運"""
        service = DeliveryService()
        fee = service.calculate_delivery_fee(1.5)
        assert fee == 0

    @pytest.mark.unit
    def test_calculate_delivery_fee_mid_tier(self):
        """2-3.5km 運費 $30"""
        service = DeliveryService()
        fee = service.calculate_delivery_fee(3.0)
        assert fee == 30

    @pytest.mark.unit
    def test_calculate_delivery_fee_far_tier(self):
        """3.5-5km 運費 $50"""
        service = DeliveryService()
        fee = service.calculate_delivery_fee(4.5)
        assert fee == 50

    @pytest.mark.unit
    def test_calculate_delivery_fee_beyond_max(self):
        """超出最大距離仍回傳最高運費"""
        service = DeliveryService()
        fee = service.calculate_delivery_fee(10.0)
        assert fee == 50

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_delivery_address_without_google_maps(self):
        """未啟用 Google Maps 時使用手動審核模式"""
        service = DeliveryService()
        # 預設 google_maps_enabled=False，走手動審核
        result = await service.validate_delivery_address("台中市中區興中街20號")

        assert result.is_valid is True
        assert result.delivery_fee == 30  # 預設運費

    @pytest.mark.unit
    @pytest.mark.slow
    def test_google_maps_integration(self):
        """Google Maps API 整合測試（需要有效 API Key）"""
        pytest.skip("需要有效的 Google Maps API Key")
