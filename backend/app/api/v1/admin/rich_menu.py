"""
管理後台 - Rich Menu 管理 API

提供 LINE Rich Menu 的列表、建立、設為預設及刪除功能
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import httpx

from app.api.deps import CurrentAdmin
from app.core.config import settings


router = APIRouter(prefix="/rich-menu", tags=["Admin - Rich Menu"])


# ==================== Schemas ====================

class RichMenuArea(BaseModel):
    """Rich Menu 區域"""
    x: int
    y: int
    width: int
    height: int
    action_type: str = "uri"  # uri, message, postback
    action_value: str = ""
    action_label: Optional[str] = None


class RichMenuCreateRequest(BaseModel):
    """建立 Rich Menu 請求"""
    name: str = "便當訂購選單"
    chat_bar_text: str = "點擊開啟選單"
    selected: bool = False
    size_width: int = 2500
    size_height: int = 1686


# ==================== 輔助函式 ====================

def _get_line_headers() -> dict:
    """取得 LINE API 請求標頭"""
    token = settings.LINE_CHANNEL_ACCESS_TOKEN or settings.line_channel_access_token
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _build_default_rich_menu(request: RichMenuCreateRequest) -> dict:
    """建立預設 Rich Menu 範本

    2x3 格局，每格為一個功能按鈕：
    | 立即訂購 | 我的訂單 | 優惠券 |
    | 店家資訊 | 會員中心 | 聯絡我們 |
    """
    w = request.size_width
    h = request.size_height
    col_w = w // 3
    row_h = h // 2

    areas = [
        # 第一排
        {
            "bounds": {"x": 0, "y": 0, "width": col_w, "height": row_h},
            "action": {
                "type": "uri",
                "label": "立即訂購",
                "uri": f"https://liff.line.me/{settings.line_liff_id}",
            },
        },
        {
            "bounds": {"x": col_w, "y": 0, "width": col_w, "height": row_h},
            "action": {
                "type": "uri",
                "label": "我的訂單",
                "uri": f"https://liff.line.me/{settings.line_liff_id}/orders",
            },
        },
        {
            "bounds": {"x": col_w * 2, "y": 0, "width": col_w, "height": row_h},
            "action": {
                "type": "uri",
                "label": "優惠券",
                "uri": f"https://liff.line.me/{settings.line_liff_id}/coupons",
            },
        },
        # 第二排
        {
            "bounds": {"x": 0, "y": row_h, "width": col_w, "height": row_h},
            "action": {
                "type": "message",
                "label": "店家資訊",
                "text": "店家資訊",
            },
        },
        {
            "bounds": {"x": col_w, "y": row_h, "width": col_w, "height": row_h},
            "action": {
                "type": "uri",
                "label": "會員中心",
                "uri": f"https://liff.line.me/{settings.line_liff_id}/profile",
            },
        },
        {
            "bounds": {"x": col_w * 2, "y": row_h, "width": col_w, "height": row_h},
            "action": {
                "type": "message",
                "label": "聯絡我們",
                "text": "聯絡我們",
            },
        },
    ]

    return {
        "size": {"width": w, "height": h},
        "selected": request.selected,
        "name": request.name,
        "chatBarText": request.chat_bar_text,
        "areas": areas,
    }


# ==================== API 端點 ====================

@router.get("/list")
async def list_rich_menus(
    admin: CurrentAdmin,
):
    """
    列出所有 Rich Menu

    呼叫 LINE API 取得目前所有 Rich Menu 清單。
    """
    headers = _get_line_headers()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                "https://api.line.me/v2/bot/richmenu/list",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"無法取得 Rich Menu 列表: {str(e)}",
            )

    # 取得目前預設 Rich Menu ID
    default_rich_menu_id = None
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                "https://api.line.me/v2/bot/user/all/richmenu",
                headers=headers,
            )
            if resp.status_code == 200:
                default_rich_menu_id = resp.json().get("richMenuId")
        except httpx.HTTPError:
            pass

    rich_menus = data.get("richmenus", [])
    for menu in rich_menus:
        menu["is_default"] = menu.get("richMenuId") == default_rich_menu_id

    return {
        "rich_menus": rich_menus,
        "default_rich_menu_id": default_rich_menu_id,
    }


@router.post("/create")
async def create_rich_menu(
    request: RichMenuCreateRequest,
    admin: CurrentAdmin,
):
    """
    建立 Rich Menu

    使用預設 2x3 範本建立 Rich Menu，包含訂購、訂單、優惠券、
    店家資訊、會員中心、聯絡我們等功能區塊。
    """
    headers = _get_line_headers()
    body = _build_default_rich_menu(request)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                "https://api.line.me/v2/bot/richmenu",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"建立 Rich Menu 失敗: {str(e)}",
            )

    return {
        "message": "Rich Menu 已建立",
        "rich_menu_id": data.get("richMenuId"),
    }


@router.post("/{rich_menu_id}/set-default")
async def set_default_rich_menu(
    rich_menu_id: str,
    admin: CurrentAdmin,
):
    """
    設定預設 Rich Menu

    將指定的 Rich Menu 設為所有使用者的預設選單。
    """
    headers = _get_line_headers()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                f"https://api.line.me/v2/user/all/richmenu/{rich_menu_id}",
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"設定預設 Rich Menu 失敗: {str(e)}",
            )

    return {
        "message": "已設為預設 Rich Menu",
        "rich_menu_id": rich_menu_id,
    }


@router.delete("/{rich_menu_id}")
async def delete_rich_menu(
    rich_menu_id: str,
    admin: CurrentAdmin,
):
    """
    刪除 Rich Menu
    """
    headers = _get_line_headers()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.delete(
                f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}",
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"刪除 Rich Menu 失敗: {str(e)}",
            )

    return {
        "message": "Rich Menu 已刪除",
        "rich_menu_id": rich_menu_id,
    }
