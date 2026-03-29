"""
配送服務

處理地址驗證、距離計算和運費試算
"""
import logging
import math
from dataclasses import dataclass
from typing import Optional, Tuple
from decimal import Decimal

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    """地理位置"""
    latitude: float
    longitude: float
    formatted_address: Optional[str] = None


@dataclass
class DistanceResult:
    """距離計算結果"""
    distance_km: float
    duration_minutes: int
    origin_address: str
    destination_address: str


@dataclass
class DeliveryValidationResult:
    """配送驗證結果"""
    is_valid: bool
    distance_km: float
    delivery_fee: int
    error_message: Optional[str] = None
    formatted_address: Optional[str] = None
    estimated_minutes: Optional[int] = None


class DeliveryService:
    """
    配送服務
    
    負責處理：
    1. 地址驗證（使用 Google Geocoding API）
    2. 距離計算（使用 Google Distance Matrix API 或 Haversine 公式）
    3. 運費試算（根據距離階梯計費）
    4. 配送範圍驗證
    """
    
    def __init__(self):
        self.api_key = settings.google_maps_api_key
        self.enabled = settings.google_maps_enabled and bool(self.api_key)
        self.store_location = GeoLocation(
            latitude=settings.store_latitude,
            longitude=settings.store_longitude,
            formatted_address=settings.store_address
        )
        self.max_distance = settings.max_delivery_distance_km
        self.fee_tiers = settings.delivery_fee_tiers
    
    async def geocode_address(self, address: str) -> Optional[GeoLocation]:
        """
        將地址轉換為經緯度
        
        Args:
            address: 地址字串
            
        Returns:
            GeoLocation: 地理位置，若失敗回傳 None
        """
        if not self.enabled:
            logger.warning("Google Maps API 未啟用，無法進行地址轉換")
            return None
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.api_key,
            "language": "zh-TW",
            "region": "TW"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
            
            if data.get("status") != "OK":
                logger.error(f"Geocoding 失敗: {data.get('status')} - {address}")
                return None
            
            result = data["results"][0]
            location = result["geometry"]["location"]
            
            return GeoLocation(
                latitude=location["lat"],
                longitude=location["lng"],
                formatted_address=result["formatted_address"]
            )
            
        except Exception as e:
            logger.error(f"Geocoding API 錯誤: {e}")
            return None
    
    async def calculate_distance_google(
        self,
        origin: GeoLocation,
        destination: GeoLocation
    ) -> Optional[DistanceResult]:
        """
        使用 Google Distance Matrix API 計算距離
        
        Args:
            origin: 起點位置
            destination: 終點位置
            
        Returns:
            DistanceResult: 距離結果
        """
        if not self.enabled:
            return None
        
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{origin.latitude},{origin.longitude}",
            "destinations": f"{destination.latitude},{destination.longitude}",
            "key": self.api_key,
            "language": "zh-TW",
            "mode": "driving"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
            
            if data.get("status") != "OK":
                logger.error(f"Distance Matrix 失敗: {data.get('status')}")
                return None
            
            element = data["rows"][0]["elements"][0]
            
            if element.get("status") != "OK":
                logger.error(f"距離計算失敗: {element.get('status')}")
                return None
            
            distance_meters = element["distance"]["value"]
            duration_seconds = element["duration"]["value"]
            
            return DistanceResult(
                distance_km=round(distance_meters / 1000, 2),
                duration_minutes=round(duration_seconds / 60),
                origin_address=data["origin_addresses"][0],
                destination_address=data["destination_addresses"][0]
            )
            
        except Exception as e:
            logger.error(f"Distance Matrix API 錯誤: {e}")
            return None
    
    def calculate_distance_haversine(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        使用 Haversine 公式計算兩點間的直線距離
        
        這是備用方案，當 Google Maps API 不可用時使用
        
        Args:
            lat1, lon1: 起點經緯度
            lat2, lon2: 終點經緯度
            
        Returns:
            float: 距離（公里）
        """
        R = 6371  # 地球半徑（公里）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return round(R * c, 2)
    
    def calculate_delivery_fee(self, distance_km: float) -> int:
        """
        根據距離計算運費
        
        依據配送距離階梯計費
        
        Args:
            distance_km: 距離（公里）
            
        Returns:
            int: 運費金額
        """
        # 將階梯轉換為排序列表
        sorted_tiers = sorted(self.fee_tiers.items())
        
        for max_distance, fee in sorted_tiers:
            if distance_km <= max_distance:
                return fee
        
        # 超出最大配送範圍，使用最高運費
        if sorted_tiers:
            return sorted_tiers[-1][1]
        
        return 0
    
    async def validate_delivery_address(
        self,
        address: str
    ) -> DeliveryValidationResult:
        """
        驗證配送地址
        
        1. 驗證地址有效性
        2. 計算與店家的距離
        3. 檢查是否在配送範圍內
        4. 計算運費
        
        Args:
            address: 配送地址
            
        Returns:
            DeliveryValidationResult: 驗證結果
        """
        # 若 Google Maps API 未啟用，使用手動審核模式
        if not self.enabled:
            return DeliveryValidationResult(
                is_valid=True,
                distance_km=0,
                delivery_fee=30,  # 預設運費
                formatted_address=address,
                error_message=None,
                estimated_minutes=None
            )
        
        # 1. 地址轉換
        location = await self.geocode_address(address)
        
        if not location:
            return DeliveryValidationResult(
                is_valid=False,
                distance_km=0,
                delivery_fee=0,
                error_message="無法識別此地址，請確認地址正確性"
            )
        
        # 2. 計算距離
        distance_result = await self.calculate_distance_google(
            self.store_location,
            location
        )
        
        if distance_result:
            distance_km = distance_result.distance_km
            estimated_minutes = distance_result.duration_minutes
        else:
            # 備用：使用 Haversine 公式
            distance_km = self.calculate_distance_haversine(
                self.store_location.latitude,
                self.store_location.longitude,
                location.latitude,
                location.longitude
            )
            # 預估時間（假設平均時速 30km/h）
            estimated_minutes = round(distance_km / 30 * 60)
        
        # 3. 檢查配送範圍
        if distance_km > self.max_distance:
            return DeliveryValidationResult(
                is_valid=False,
                distance_km=distance_km,
                delivery_fee=0,
                formatted_address=location.formatted_address,
                error_message=f"超出配送範圍（最遠 {self.max_distance} 公里），您的距離約 {distance_km} 公里"
            )
        
        # 4. 計算運費
        delivery_fee = self.calculate_delivery_fee(distance_km)
        
        return DeliveryValidationResult(
            is_valid=True,
            distance_km=distance_km,
            delivery_fee=delivery_fee,
            formatted_address=location.formatted_address,
            estimated_minutes=estimated_minutes
        )
    
    async def calculate_route_info(
        self,
        destination_address: str
    ) -> Optional[dict]:
        """
        計算配送路線資訊
        
        Args:
            destination_address: 目的地址
            
        Returns:
            dict: 路線資訊
        """
        validation = await self.validate_delivery_address(destination_address)
        
        return {
            "is_valid": validation.is_valid,
            "distance_km": validation.distance_km,
            "delivery_fee": validation.delivery_fee,
            "formatted_address": validation.formatted_address,
            "estimated_minutes": validation.estimated_minutes,
            "error_message": validation.error_message,
            "store_address": self.store_location.formatted_address,
            "max_distance_km": self.max_distance,
            "free_delivery_distance_km": min(self.fee_tiers.keys()) if self.fee_tiers else 0
        }


# 全域實例
delivery_service = DeliveryService()


def get_delivery_service() -> DeliveryService:
    """取得配送服務實例"""
    return delivery_service
