"""
LINE Webhook API

處理來自 LINE 的 Webhook 事件
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

from app.services.line_messaging import line_messaging
from app.core.config import settings

router = APIRouter(prefix="/webhook", tags=["LINE Webhook"])


# ==================== Schemas ====================

class WebhookEvent(BaseModel):
    """Webhook 事件"""
    type: str
    timestamp: int
    source: Dict[str, Any]
    replyToken: str | None = None
    message: Dict[str, Any] | None = None
    postback: Dict[str, Any] | None = None


class WebhookRequest(BaseModel):
    """Webhook 請求"""
    destination: str
    events: List[WebhookEvent]


# ==================== API 端點 ====================

@router.post("")
async def handle_webhook(
    request: Request,
    x_line_signature: str = Header(..., alias="X-Line-Signature"),
):
    """
    處理 LINE Webhook 事件
    
    驗證簽名並處理各種事件類型
    """
    # 取得請求 body
    body = await request.body()

    # 驗證簽名
    if not line_messaging.verify_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="簽名驗證失敗")

    # 解析事件
    try:
        data = await request.json()
        events = data.get("events", [])
    except Exception:
        raise HTTPException(status_code=400, detail="無效的請求格式")

    # 處理每個事件
    for event in events:
        await handle_event(event)

    return {"status": "ok"}


async def handle_event(event: Dict[str, Any]) -> None:
    """
    處理單一事件
    """
    event_type = event.get("type")
    reply_token = event.get("replyToken")

    if event_type == "message":
        await handle_message_event(event, reply_token)
    elif event_type == "follow":
        await handle_follow_event(event, reply_token)
    elif event_type == "unfollow":
        await handle_unfollow_event(event)
    elif event_type == "postback":
        await handle_postback_event(event, reply_token)


async def handle_message_event(event: Dict[str, Any], reply_token: str | None) -> None:
    """
    處理訊息事件
    """
    message = event.get("message", {})
    message_type = message.get("type")
    text = message.get("text", "")

    if message_type != "text" or not reply_token:
        return

    # 關鍵字回覆
    response_messages = []

    if "菜單" in text or "menu" in text.lower():
        response_messages = [
            {
                "type": "text",
                "text": "🍱 歡迎光臨一米粒！\n\n請點擊下方連結查看完整菜單：\nhttps://liff.line.me/{settings.line_liff_id}/menu",
            }
        ]
    elif "訂單" in text or "order" in text.lower():
        response_messages = [
            {
                "type": "text",
                "text": "📋 查詢訂單\n\n請點擊下方連結查看訂單紀錄：\nhttps://liff.line.me/{settings.line_liff_id}/orders",
            }
        ]
    elif "營業" in text or "時間" in text:
        response_messages = [
            {
                "type": "text",
                "text": "⏰ 營業時間\n\n週一至週五：10:00 - 16:30\n週六、週日：公休\n\n📍 地址：台中市中區興中街20號\n📞 電話：0909-998-952",
            }
        ]
    elif "外送" in text or "配送" in text:
        response_messages = [
            {
                "type": "text",
                "text": "🚗 外送服務\n\n外送範圍：店家周邊 3 公里\n外送費用：$30\n滿 $300 免運費\n\n* 外送僅限平日營業時間",
            }
        ]
    else:
        response_messages = [
            {
                "type": "text",
                "text": "您好！感謝您聯繫一米粒 🍱\n\n您可以輸入以下關鍵字：\n• 菜單 - 查看菜單\n• 訂單 - 查詢訂單\n• 營業時間 - 營業資訊\n• 外送 - 外送說明\n\n或直接點擊下方選單開始訂餐！",
            }
        ]

    if response_messages:
        await line_messaging.reply_message(reply_token, response_messages)


async def handle_follow_event(event: Dict[str, Any], reply_token: str | None) -> None:
    """
    處理新增好友事件
    """
    if not reply_token:
        return

    # 歡迎訊息
    welcome_message = {
        "type": "flex",
        "altText": "歡迎加入一米粒！",
        "contents": {
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🍱",
                        "size": "5xl",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#fff7ed",
                "paddingAll": "24px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "歡迎加入一米粒！",
                        "weight": "bold",
                        "size": "xl",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "弁当専門店",
                        "size": "md",
                        "color": "#f97316",
                        "align": "center",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "每天為您準備新鮮美味的便當\n現在就來訂餐吧！",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "lg",
                        "wrap": True,
                        "align": "center"
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "立即訂餐",
                            "uri": "https://liff.line.me/{settings.line_liff_id}"
                        },
                        "style": "primary",
                        "color": "#f97316"
                    }
                ],
                "paddingAll": "16px"
            }
        }
    }

    await line_messaging.reply_message(reply_token, [welcome_message])


async def handle_unfollow_event(event: Dict[str, Any]) -> None:
    """
    處理取消好友事件

    記錄使用者取消追蹤（不刪除帳號，保留訂單紀錄）
    """
    import logging
    user_id = event.get("source", {}).get("userId")
    if user_id:
        logging.getLogger(__name__).info(f"使用者取消追蹤: {user_id}")


async def handle_postback_event(event: Dict[str, Any], reply_token: str | None) -> None:
    """
    處理 Postback 事件
    """
    if not reply_token:
        return

    postback_data = event.get("postback", {}).get("data", "")

    # 解析 postback data（格式: action=xxx&param=yyy）
    params = dict(param.split("=") for param in postback_data.split("&") if "=" in param)
    action = params.get("action")

    if action == "view_order":
        order_id = params.get("order_id", "")
        liff_url = f"https://liff.line.me/{settings.line_liff_id}/orders/{order_id}" if order_id else f"https://liff.line.me/{settings.line_liff_id}/orders"
        await line_messaging.reply_message(reply_token, [
            {
                "type": "text",
                "text": f"📋 點擊查看訂單詳情：\n{liff_url}",
            }
        ])
    elif action == "reorder":
        liff_url = f"https://liff.line.me/{settings.line_liff_id}/menu"
        await line_messaging.reply_message(reply_token, [
            {
                "type": "text",
                "text": f"🍱 歡迎再次訂購！\n點擊前往菜單：\n{liff_url}",
            }
        ])
