"""
日誌配置

設定結構化日誌輸出，支援 JSON 格式用於生產環境
"""
import logging
import sys
from typing import Optional
import json
from datetime import datetime

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """
    JSON 格式化器
    
    將日誌輸出為 JSON 格式，方便日誌聚合工具處理
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加額外資訊
        if hasattr(record, "request_id"):
            log_dict["request_id"] = record.request_id
        
        # 添加異常資訊
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_dict, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    彩色格式化器
    
    用於開發環境的終端輸出
    """
    
    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 綠色
        "WARNING": "\033[33m",   # 黃色
        "ERROR": "\033[31m",     # 紅色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: Optional[str] = None,
    json_format: bool = False
) -> None:
    """
    設定日誌配置
    
    Args:
        level: 日誌級別（DEBUG, INFO, WARNING, ERROR）
        json_format: 是否使用 JSON 格式
    """
    # 確定日誌級別
    if level is None:
        level = "DEBUG" if settings.debug else "INFO"
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 建立根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除現有處理器
    root_logger.handlers.clear()
    
    # 建立控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 選擇格式化器
    if json_format or not settings.debug:
        formatter = JsonFormatter()
    else:
        formatter = ColoredFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 設定第三方庫日誌級別
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logging.info(f"日誌系統已初始化 (level={level}, json={json_format})")


def get_logger(name: str) -> logging.Logger:
    """
    取得指定名稱的日誌器
    
    Args:
        name: 日誌器名稱（通常使用 __name__）
        
    Returns:
        logging.Logger: 日誌器實例
    """
    return logging.getLogger(name)
