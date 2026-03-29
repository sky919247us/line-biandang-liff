"""
效能監控中間件

提供請求追蹤、效能計量和日誌記錄功能
"""
import time
import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    效能監控中間件
    
    功能：
    1. 為每個請求生成唯一追蹤 ID
    2. 記錄請求處理時間
    3. 記錄請求和回應資訊
    4. 檢測慢速請求
    """
    
    # 慢速請求閾值（毫秒）
    SLOW_REQUEST_THRESHOLD_MS = 1000
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成請求追蹤 ID
        request_id = str(uuid.uuid4())[:8]
        
        # 記錄開始時間
        start_time = time.perf_counter()
        
        # 設定請求 ID 到 state
        request.state.request_id = request_id
        
        # 處理請求
        try:
            response = await call_next(request)
        except Exception as e:
            # 記錄異常
            logger.error(
                f"[{request_id}] Request failed: {request.method} {request.url.path}",
                exc_info=True
            )
            raise
        
        # 計算處理時間
        process_time_ms = (time.perf_counter() - start_time) * 1000
        
        # 添加追蹤標頭
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
        
        # 記錄請求日誌
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        elif process_time_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            log_level = logging.WARNING
        
        log_message = (
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({process_time_ms:.2f}ms)"
        )
        
        if process_time_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            log_message += " [SLOW]"
        
        logger.log(log_level, log_message)
        
        return response


class RequestStatsMiddleware(BaseHTTPMiddleware):
    """
    請求統計中間件
    
    收集：
    1. 總請求數
    2. 成功/失敗請求數
    3. 平均回應時間
    4. 最慢端點
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "error_requests": 0,
            "total_time_ms": 0,
            "slowest_endpoint": None,
            "slowest_time_ms": 0,
            "endpoint_stats": {}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time_ms = (time.perf_counter() - start_time) * 1000
        
        # 更新統計
        self.stats["total_requests"] += 1
        self.stats["total_time_ms"] += process_time_ms
        
        if response.status_code < 400:
            self.stats["success_requests"] += 1
        else:
            self.stats["error_requests"] += 1
        
        # 追蹤最慢端點
        if process_time_ms > self.stats["slowest_time_ms"]:
            self.stats["slowest_endpoint"] = request.url.path
            self.stats["slowest_time_ms"] = process_time_ms
        
        # 端點統計
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in self.stats["endpoint_stats"]:
            self.stats["endpoint_stats"][endpoint] = {
                "count": 0,
                "total_time_ms": 0,
                "errors": 0
            }
        
        self.stats["endpoint_stats"][endpoint]["count"] += 1
        self.stats["endpoint_stats"][endpoint]["total_time_ms"] += process_time_ms
        if response.status_code >= 400:
            self.stats["endpoint_stats"][endpoint]["errors"] += 1
        
        return response
    
    def get_stats(self) -> dict:
        """取得統計資料"""
        avg_time = 0
        if self.stats["total_requests"] > 0:
            avg_time = self.stats["total_time_ms"] / self.stats["total_requests"]
        
        return {
            "total_requests": self.stats["total_requests"],
            "success_requests": self.stats["success_requests"],
            "error_requests": self.stats["error_requests"],
            "success_rate": (
                self.stats["success_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "avg_response_time_ms": round(avg_time, 2),
            "slowest_endpoint": self.stats["slowest_endpoint"],
            "slowest_time_ms": round(self.stats["slowest_time_ms"], 2)
        }
    
    def get_endpoint_stats(self) -> list:
        """取得端點統計"""
        result = []
        for endpoint, stats in self.stats["endpoint_stats"].items():
            avg_time = stats["total_time_ms"] / stats["count"] if stats["count"] > 0 else 0
            result.append({
                "endpoint": endpoint,
                "count": stats["count"],
                "avg_time_ms": round(avg_time, 2),
                "errors": stats["errors"],
                "error_rate": round(
                    stats["errors"] / stats["count"] * 100 if stats["count"] > 0 else 0,
                    2
                )
            })
        
        # 按請求數排序
        result.sort(key=lambda x: x["count"], reverse=True)
        return result
