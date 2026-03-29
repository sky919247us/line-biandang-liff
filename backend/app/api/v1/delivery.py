"""
配送 API 路由

處理配送相關的地址驗證、距離計算和運費試算
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.delivery_service import delivery_service
from app.core.config import settings


router = APIRouter(prefix="/delivery", tags=["配送"])


class AddressValidationRequest(BaseModel):
    """地址驗證請求"""
    address: str


class AddressValidationResponse(BaseModel):
    """地址驗證回應"""
    is_valid: bool
    distance_km: float
    delivery_fee: int
    formatted_address: Optional[str] = None
    estimated_minutes: Optional[int] = None
    error_message: Optional[str] = None


class DeliveryFeeRequest(BaseModel):
    """運費計算請求"""
    address: str
    subtotal: float = 0  # 訂單小計，用於判斷滿額免運


class DeliveryFeeResponse(BaseModel):
    """運費計算回應"""
    is_valid: bool
    distance_km: float
    base_delivery_fee: int
    final_delivery_fee: int  # 考慮滿額免運後的運費
    free_delivery_threshold: float
    is_free_delivery: bool
    formatted_address: Optional[str] = None
    estimated_minutes: Optional[int] = None
    error_message: Optional[str] = None


class DeliveryInfoResponse(BaseModel):
    """配送資訊回應"""
    delivery_enabled: bool
    google_maps_enabled: bool
    max_distance_km: float
    min_order_amount: float
    free_delivery_threshold: float
    store_address: str
    fee_tiers: dict
    business_hours_start: str
    business_hours_end: str


@router.get("/info", response_model=DeliveryInfoResponse)
async def get_delivery_info():
    """
    取得配送設定資訊
    
    回傳配送範圍、運費階梯、最低消費等設定
    """
    # 計算免運門檻（取運費為 0 的最大距離）
    free_delivery_km = 0
    for distance, fee in settings.delivery_fee_tiers.items():
        if fee == 0 and distance > free_delivery_km:
            free_delivery_km = distance
    
    return DeliveryInfoResponse(
        delivery_enabled=True,
        google_maps_enabled=settings.google_maps_enabled,
        max_distance_km=settings.max_delivery_distance_km,
        min_order_amount=settings.min_order_amount,
        free_delivery_threshold=300,  # 滿額免運門檻
        store_address=settings.store_address,
        fee_tiers=settings.delivery_fee_tiers,
        business_hours_start=settings.business_hours_start,
        business_hours_end=settings.business_hours_end
    )


@router.post("/validate-address", response_model=AddressValidationResponse)
async def validate_address(request: AddressValidationRequest):
    """
    驗證配送地址
    
    1. 驗證地址有效性
    2. 計算與店家距離
    3. 檢查是否在配送範圍內
    4. 計算基本運費
    """
    if not request.address or len(request.address.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請輸入完整的配送地址"
        )
    
    result = await delivery_service.validate_delivery_address(request.address)
    
    return AddressValidationResponse(
        is_valid=result.is_valid,
        distance_km=result.distance_km,
        delivery_fee=result.delivery_fee,
        formatted_address=result.formatted_address,
        estimated_minutes=result.estimated_minutes,
        error_message=result.error_message
    )


@router.post("/calculate", response_model=DeliveryFeeResponse)
async def calculate_delivery_fee(request: DeliveryFeeRequest):
    """
    計算配送運費
    
    包含滿額免運邏輯
    """
    if not request.address or len(request.address.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請輸入完整的配送地址"
        )
    
    result = await delivery_service.validate_delivery_address(request.address)
    
    # 滿額免運門檻
    free_delivery_threshold = 300
    
    # 判斷是否滿額免運
    is_free_delivery = request.subtotal >= free_delivery_threshold
    final_fee = 0 if is_free_delivery else result.delivery_fee
    
    return DeliveryFeeResponse(
        is_valid=result.is_valid,
        distance_km=result.distance_km,
        base_delivery_fee=result.delivery_fee,
        final_delivery_fee=final_fee,
        free_delivery_threshold=free_delivery_threshold,
        is_free_delivery=is_free_delivery,
        formatted_address=result.formatted_address,
        estimated_minutes=result.estimated_minutes,
        error_message=result.error_message
    )


@router.post("/route-info")
async def get_route_info(request: AddressValidationRequest):
    """
    取得完整配送路線資訊
    
    包含距離、運費、預估時間等
    """
    if not request.address or len(request.address.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請輸入完整的配送地址"
        )
    
    route_info = await delivery_service.calculate_route_info(request.address)
    
    return route_info
