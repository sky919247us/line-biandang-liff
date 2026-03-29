"""
管理後台 - 群發訊息 API

提供 LINE 群發訊息、受眾分群統計及訊息預覽功能
"""
import uuid
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, distinct
import httpx

from app.api.deps import DbSession, CurrentAdmin
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.core.config import settings


router = APIRouter(prefix="/broadcast", tags=["Admin - Broadcast"])


# ==================== Schemas ====================

class BroadcastMessage(BaseModel):
    """群發訊息請求"""
    message_type: str = "text"  # text, flex
    text: Optional[str] = None
    alt_text: Optional[str] = None
    flex_contents: Optional[dict] = None


class BroadcastRequest(BaseModel):
    """群發請求"""
    target: str = "all"  # all, active, inactive, custom
    days_inactive: Optional[int] = 30  # for inactive targeting
    user_ids: Optional[List[str]] = None  # for custom targeting
    message: BroadcastMessage


class BroadcastLog(BaseModel):
    """群發紀錄"""
    id: str
    target: str
    target_count: int
    message_type: str
    message_preview: str
    sent_at: datetime
    status: str


class SegmentInfo(BaseModel):
    """受眾分群資訊"""
    all_users: int
    active_users: int
    inactive_users: int
    new_users: int


# ==================== 輔助函式 ====================

def _get_line_headers() -> dict:
    """取得 LINE API 請求標頭"""
    token = settings.LINE_CHANNEL_ACCESS_TOKEN or settings.line_channel_access_token
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _build_messages(message: BroadcastMessage) -> List[dict]:
    """根據訊息類型建立 LINE 訊息陣列"""
    if message.message_type == "flex":
        if not message.flex_contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Flex 訊息需要提供 flex_contents",
            )
        return [
            {
                "type": "flex",
                "altText": message.alt_text or "訊息通知",
                "contents": message.flex_contents,
            }
        ]
    else:
        # text
        if not message.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文字訊息需要提供 text",
            )
        return [{"type": "text", "text": message.text}]


def _get_target_user_ids(
    db,
    target: str,
    days_inactive: int = 30,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """根據目標類型查詢使用者 LINE ID"""
    now = datetime.now()

    if target == "custom":
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="自訂目標需要提供 user_ids",
            )
        users = (
            db.query(User.line_user_id)
            .filter(
                User.line_user_id.isnot(None),
                User.line_user_id != "",
                User.id.in_(user_ids),
            )
            .all()
        )
        return [u.line_user_id for u in users]

    if target == "active":
        # 近 30 天有下單
        thirty_days_ago = now - timedelta(days=30)
        active_user_ids = (
            db.query(distinct(Order.user_id))
            .filter(
                Order.created_at >= thirty_days_ago,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .all()
        )
        active_ids = [r[0] for r in active_user_ids]
        users = (
            db.query(User.line_user_id)
            .filter(
                User.line_user_id.isnot(None),
                User.line_user_id != "",
                User.id.in_(active_ids),
            )
            .all()
        )
        return [u.line_user_id for u in users]

    if target == "inactive":
        # 超過 X 天未下單
        cutoff = now - timedelta(days=days_inactive)
        active_user_ids = (
            db.query(distinct(Order.user_id))
            .filter(
                Order.created_at >= cutoff,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .all()
        )
        active_ids = {r[0] for r in active_user_ids}
        users = (
            db.query(User.line_user_id)
            .filter(
                User.line_user_id.isnot(None),
                User.line_user_id != "",
            )
            .all()
        )
        # 所有使用者中排除活躍使用者
        all_users_q = (
            db.query(User.id, User.line_user_id)
            .filter(
                User.line_user_id.isnot(None),
                User.line_user_id != "",
            )
            .all()
        )
        return [u.line_user_id for u in all_users_q if u.id not in active_ids]

    # target == "all"
    users = (
        db.query(User.line_user_id)
        .filter(
            User.line_user_id.isnot(None),
            User.line_user_id != "",
        )
        .all()
    )
    return [u.line_user_id for u in users]


# ==================== API 端點 ====================

@router.post("/send")
async def send_broadcast(
    request: BroadcastRequest,
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    群發訊息

    根據目標類型查詢使用者，透過 LINE Messaging API multicast 送出訊息。
    multicast 每次最多 500 個使用者，超過時會分批發送。
    """
    # 取得目標使用者
    target_ids = _get_target_user_ids(
        db, request.target, request.days_inactive or 30, request.user_ids
    )

    if not target_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="找不到符合條件的使用者",
        )

    # 建立訊息
    messages = _build_messages(request.message)

    # 分批發送（每批最多 500 個）
    headers = _get_line_headers()
    success_count = 0
    fail_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(target_ids), 500):
            batch = target_ids[i : i + 500]
            try:
                response = await client.post(
                    "https://api.line.me/v2/bot/message/multicast",
                    headers=headers,
                    json={"to": batch, "messages": messages},
                )
                response.raise_for_status()
                success_count += len(batch)
            except httpx.HTTPError as e:
                print(f"群發訊息失敗 (batch {i}): {e}")
                fail_count += len(batch)

    return {
        "message": "群發訊息已發送",
        "target": request.target,
        "total_targets": len(target_ids),
        "success_count": success_count,
        "fail_count": fail_count,
        "sent_at": datetime.now().isoformat(),
    }


@router.get("/segments", response_model=SegmentInfo)
async def get_segments(
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    取得受眾分群統計

    - all_users: 所有擁有 LINE ID 的使用者數
    - active_users: 近 30 天有下單
    - inactive_users: 超過 30 天未下單
    - new_users: 本月新加入
    """
    now = datetime.now()

    # 所有使用者（有 LINE ID）
    all_users = (
        db.query(func.count(User.id))
        .filter(
            User.line_user_id.isnot(None),
            User.line_user_id != "",
        )
        .scalar()
        or 0
    )

    # 近 30 天活躍
    thirty_days_ago = now - timedelta(days=30)
    active_users = (
        db.query(func.count(distinct(Order.user_id)))
        .filter(
            Order.created_at >= thirty_days_ago,
            Order.status != OrderStatus.CANCELLED.value,
        )
        .scalar()
        or 0
    )

    # 不活躍 = 全部 - 活躍
    inactive_users = max(all_users - active_users, 0)

    # 本月新使用者
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users = (
        db.query(func.count(User.id))
        .filter(
            User.line_user_id.isnot(None),
            User.line_user_id != "",
            User.created_at >= month_start,
        )
        .scalar()
        or 0
    )

    return SegmentInfo(
        all_users=all_users,
        active_users=active_users,
        inactive_users=inactive_users,
        new_users=new_users,
    )


@router.post("/preview")
async def preview_broadcast(
    request: BroadcastRequest,
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    預覽群發訊息

    回傳格式化後的訊息內容及目標人數，不實際發送。
    """
    # 取得目標人數
    target_ids = _get_target_user_ids(
        db, request.target, request.days_inactive or 30, request.user_ids
    )

    # 建立訊息
    messages = _build_messages(request.message)

    # 訊息預覽文字
    if request.message.message_type == "flex":
        preview_text = request.message.alt_text or "Flex 訊息"
    else:
        preview_text = (request.message.text or "")[:100]

    return {
        "target": request.target,
        "target_count": len(target_ids),
        "messages": messages,
        "preview_text": preview_text,
    }
