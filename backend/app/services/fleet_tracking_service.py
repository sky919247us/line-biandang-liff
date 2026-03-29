"""
外送車隊追蹤服務

整合 Lalamove / UberDirect API 進行外送追蹤
目前為預留介面
"""
import logging
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FleetProvider(str, Enum):
    LALAMOVE = "lalamove"
    UBER_DIRECT = "uber_direct"
    SELF = "self"  # 自有車隊


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryInfo(BaseModel):
    """外送追蹤資訊"""
    order_id: str
    provider: str
    external_order_id: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    status: str = "pending"
    estimated_arrival: Optional[str] = None
    tracking_url: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


class FleetTrackingService:
    """外送車隊追蹤服務"""

    def __init__(self, provider: FleetProvider = FleetProvider.SELF):
        self.provider = provider
        logger.info(f"FleetTrackingService initialized with provider: {provider}")

    async def create_delivery(self, order_id: str, pickup_address: str,
                               delivery_address: str, **kwargs) -> DeliveryInfo:
        """建立外送單"""
        logger.info(f"[Stub] Creating delivery for order {order_id}")
        # TODO: Call Lalamove/UberDirect API
        return DeliveryInfo(
            order_id=order_id,
            provider=self.provider.value,
            status=DeliveryStatus.PENDING.value,
        )

    async def get_delivery_status(self, order_id: str) -> DeliveryInfo:
        """查詢外送狀態"""
        logger.info(f"[Stub] Getting delivery status for order {order_id}")
        return DeliveryInfo(
            order_id=order_id,
            provider=self.provider.value,
            status=DeliveryStatus.PENDING.value,
        )

    async def cancel_delivery(self, order_id: str) -> bool:
        """取消外送"""
        logger.info(f"[Stub] Cancelling delivery for order {order_id}")
        return True

    async def get_tracking_url(self, order_id: str) -> Optional[str]:
        """取得追蹤連結"""
        # TODO: Return actual tracking URL from provider
        return None
