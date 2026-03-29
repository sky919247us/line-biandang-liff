"""
應用程式設定模組

從環境變數載入所有設定值，避免硬編碼敏感資訊
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    應用程式設定類別

    所有設定值從環境變數讀取，支援 .env 檔案
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # 應用程式基本設定
    app_name: str = "LINE 便當訂購系統"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # 安全設定
    secret_key: str = "CHANGE-ME-IN-PRODUCTION-use-python-secrets-token_hex-32"
    access_token_expire_minutes: int = 60 * 24  # 1 天（生產環境建議更短）
    
    # 資料庫設定
    database_url: str = "sqlite:///./biandang.db"
    
    # Redis 設定
    redis_url: str = "redis://localhost:6379"
    
    # LINE 設定
    line_channel_id: str = ""
    line_channel_secret: str = ""
    line_channel_access_token: str = ""  # Messaging API Token
    line_liff_id: str = ""
    
    # LINE 設定 - 大寫版本（用於相容性）
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    
    # Google Maps 設定（可選）
    google_maps_api_key: str = ""
    google_maps_enabled: bool = False
    
    # 配送設定
    max_delivery_distance_km: float = 5.0
    min_order_amount: float = 150.0
    
    # 運費階梯設定 (距離km: 運費)
    delivery_fee_tiers: dict = {
        2.0: 0,      # 0-2km 免運
        3.5: 30,     # 2-3.5km $30
        5.0: 50,     # 3.5-5km $50
    }
    
    # 店家設定（一米粒便當店：台中市中區興中街20號）
    store_latitude: float = 24.1378  # 台中市中區
    store_longitude: float = 120.6828
    store_address: str = "台中市中區興中街20號"
    
    # 營業時間設定
    business_hours_start: str = "10:00"
    business_hours_end: str = "16:30"
    
    # 每日訂單上限
    daily_order_limit: int = 100
    


@lru_cache
def get_settings() -> Settings:
    """
    取得設定單例
    
    使用 lru_cache 確保只建立一次設定實例
    """
    return Settings()


# 匯出設定實例
settings = get_settings()
