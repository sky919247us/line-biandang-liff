"""
LINE Messaging API 服務

處理 LINE 訊息推播和 Webhook
"""
import hashlib
import hmac
import base64
import logging
import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class LineMessage(BaseModel):
    """LINE 訊息基礎模型"""
    type: str
    text: Optional[str] = None
    contents: Optional[Dict[str, Any]] = None


class FlexMessage(BaseModel):
    """Flex 訊息模型"""
    type: str = "flex"
    altText: str
    contents: Dict[str, Any]


class LineMessagingService:
    """
    LINE Messaging API 服務
    
    提供訊息推播功能
    """

    def __init__(self):
        self.channel_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = settings.LINE_CHANNEL_SECRET
        self.api_base_url = "https://api.line.me/v2/bot"

    def _get_headers(self) -> Dict[str, str]:
        """取得 API 請求標頭"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}",
        }

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """
        驗證 Webhook 簽名
        
        Args:
            body: 請求 body
            signature: X-Line-Signature header
            
        Returns:
            簽名是否有效
        """
        hash_value = hmac.new(
            self.channel_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash_value).decode("utf-8")
        return hmac.compare_digest(expected_signature, signature)

    async def push_message(
        self,
        user_id: str,
        messages: List[Dict[str, Any]]
    ) -> bool:
        """
        推播訊息給指定使用者
        
        Args:
            user_id: LINE 使用者 ID
            messages: 要推播的訊息陣列
            
        Returns:
            是否成功
        """
        if not self.channel_access_token:
            logger.warning("LINE Channel Access Token 未設定")
            return False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/message/push",
                    headers=self._get_headers(),
                    json={
                        "to": user_id,
                        "messages": messages,
                    },
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                logger.error(f"推播訊息失敗: {e}")
                return False

    async def multicast(
        self,
        user_ids: List[str],
        messages: List[Dict[str, Any]]
    ) -> bool:
        """
        群發訊息給多個使用者
        
        Args:
            user_ids: LINE 使用者 ID 陣列（最多 500 個）
            messages: 要推播的訊息陣列
            
        Returns:
            是否成功
        """
        if not self.channel_access_token:
            logger.warning("LINE Channel Access Token 未設定")
            return False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/message/multicast",
                    headers=self._get_headers(),
                    json={
                        "to": user_ids[:500],  # 最多 500 個
                        "messages": messages,
                    },
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                logger.error(f"群發訊息失敗: {e}")
                return False

    async def reply_message(
        self,
        reply_token: str,
        messages: List[Dict[str, Any]]
    ) -> bool:
        """
        回覆訊息
        
        Args:
            reply_token: Reply Token
            messages: 要回覆的訊息陣列
            
        Returns:
            是否成功
        """
        if not self.channel_access_token:
            return False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/message/reply",
                    headers=self._get_headers(),
                    json={
                        "replyToken": reply_token,
                        "messages": messages,
                    },
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                logger.error(f"回覆訊息失敗: {e}")
                return False


# 單例實例
line_messaging = LineMessagingService()


# ==================== 訂單通知訊息模板 ====================

def create_order_confirmed_message(order_number: str, total: int, pickup_time: str | None) -> Dict[str, Any]:
    """
    建立訂單確認訊息
    """
    pickup_info = f"預計取餐時間：{pickup_time}" if pickup_time else "請等待備餐完成通知"
    
    return {
        "type": "flex",
        "altText": f"訂單確認 {order_number}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "✅ 訂單已確認",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#16a34a"
                    }
                ],
                "backgroundColor": "#dcfce7",
                "paddingAll": "16px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"訂單編號：{order_number}",
                        "weight": "bold",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": f"訂單金額：${total}",
                        "size": "md",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": pickup_info,
                        "size": "sm",
                        "color": "#666666",
                        "margin": "lg",
                        "wrap": True
                    }
                ],
                "paddingAll": "16px"
            }
        }
    }


def create_order_ready_message(order_number: str) -> Dict[str, Any]:
    """
    建立餐點完成訊息
    """
    return {
        "type": "flex",
        "altText": f"餐點已備妥 {order_number}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🍱 餐點已備妥",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#f97316"
                    }
                ],
                "backgroundColor": "#fff7ed",
                "paddingAll": "16px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"訂單編號：{order_number}",
                        "weight": "bold",
                        "size": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "您的餐點已經準備好囉！\n請持訂單編號至店內取餐",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "lg",
                        "wrap": True
                    }
                ],
                "paddingAll": "16px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📍 台中市中區興中街20號",
                        "size": "xs",
                        "color": "#888888",
                        "align": "center"
                    }
                ],
                "paddingAll": "12px"
            }
        }
    }


def create_order_cancelled_message(order_number: str, reason: str | None = None) -> Dict[str, Any]:
    """
    建立訂單取消訊息
    """
    reason_text = f"原因：{reason}" if reason else "如有疑問請聯繫店家"
    
    return {
        "type": "flex",
        "altText": f"訂單已取消 {order_number}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "❌ 訂單已取消",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#dc2626"
                    }
                ],
                "backgroundColor": "#fee2e2",
                "paddingAll": "16px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"訂單編號：{order_number}",
                        "weight": "bold",
                        "size": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": reason_text,
                        "size": "sm",
                        "color": "#666666",
                        "margin": "lg",
                        "wrap": True
                    }
                ],
                "paddingAll": "16px"
            }
        }
    }


def create_delivery_started_message(order_number: str, estimated_time: str) -> Dict[str, Any]:
    """
    建立外送出發訊息
    """
    return {
        "type": "flex",
        "altText": f"外送出發 {order_number}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🚗 外送已出發",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#2563eb"
                    }
                ],
                "backgroundColor": "#dbeafe",
                "paddingAll": "16px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"訂單編號：{order_number}",
                        "weight": "bold",
                        "size": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"預計送達時間：{estimated_time}",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "請準備好迎接美味的便當！",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "16px"
            }
        }
    }
