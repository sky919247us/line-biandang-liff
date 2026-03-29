"""
快取服務

提供簡單的記憶體快取和 Redis 快取支援
"""
import time
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps
from dataclasses import dataclass

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """快取條目"""
    value: Any
    expires_at: float


class MemoryCache:
    """
    記憶體快取
    
    適用於單一實例部署，重啟後資料會遺失
    """
    
    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        # 檢查是否過期
        if entry.expires_at < time.time():
            del self._cache[key]
            return None
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        設定快取值
        
        Args:
            key: 快取鍵
            value: 快取值
            ttl: 存活時間（秒），預設 5 分鐘
        """
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + ttl
        )
    
    def delete(self, key: str) -> None:
        """刪除快取"""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """清除所有快取"""
        self._cache.clear()
    
    def cleanup(self) -> int:
        """清理過期條目，回傳清理數量"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expires_at < now
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


class RedisCache:
    """
    Redis 快取
    
    適用於多實例部署
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self._redis = None
        self._redis_url = redis_url or settings.redis_url
        self._connect()
    
    def _connect(self) -> None:
        """連線到 Redis"""
        if not self._redis_url:
            logger.warning("未設定 REDIS_URL，Redis 快取已停用")
            return
        
        try:
            import redis
            self._redis = redis.from_url(self._redis_url)
            self._redis.ping()
            logger.info("Redis 快取已連線")
        except Exception as e:
            logger.warning(f"Redis 連線失敗: {e}，降級為記憶體快取")
            self._redis = None
    
    def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        if self._redis is None:
            return None
        
        try:
            value = self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis GET 失敗: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """設定快取值"""
        if self._redis is None:
            return
        
        try:
            self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Redis SET 失敗: {e}")
    
    def delete(self, key: str) -> None:
        """刪除快取"""
        if self._redis is None:
            return
        
        try:
            self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE 失敗: {e}")
    
    def clear(self, pattern: str = "*") -> None:
        """清除符合模式的快取"""
        if self._redis is None:
            return
        
        try:
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis CLEAR 失敗: {e}")


# 預設快取實例
_memory_cache = MemoryCache()
_redis_cache: Optional[RedisCache] = None


def get_cache() -> MemoryCache | RedisCache:
    """
    取得快取實例
    
    優先使用 Redis，若不可用則使用記憶體快取
    """
    global _redis_cache
    
    if settings.redis_url:
        if _redis_cache is None:
            _redis_cache = RedisCache()
        if _redis_cache._redis is not None:
            return _redis_cache
    
    return _memory_cache


def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable[..., str]] = None
):
    """
    快取裝飾器
    
    Args:
        key_prefix: 快取鍵前綴
        ttl: 存活時間（秒）
        key_builder: 自訂鍵生成函式
    
    使用範例：
        @cached("products", ttl=600)
        def get_products(category_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 建立快取鍵
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"
            
            # 嘗試從快取取得
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"快取命中: {cache_key}")
                return cached_value
            
            # 執行函式並快取結果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"快取設定: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> None:
    """
    清除符合模式的快取
    
    Args:
        pattern: 快取鍵模式
    """
    cache = get_cache()
    if isinstance(cache, RedisCache):
        cache.clear(pattern)
    else:
        # 記憶體快取需要遍歷所有鍵
        keys_to_delete = [
            key for key in _memory_cache._cache.keys()
            if key.startswith(pattern.rstrip("*"))
        ]
        for key in keys_to_delete:
            _memory_cache.delete(key)
