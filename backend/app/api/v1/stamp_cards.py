"""
集點卡 API

提供集點卡模板查詢、集點、兌換獎勵等功能
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUser
from app.models.stamp_card import StampCardTemplate, StampCard
from app.models.order import Order


router = APIRouter(prefix="/stamp-cards", tags=["集點卡"])


# ==================== Schemas ====================

class StampCardTemplateSchema(BaseModel):
    """集點卡模板 Schema"""
    model_config = {"from_attributes": True}

    id: str
    name: str
    description: Optional[str] = None
    stamps_required: int
    reward_type: str
    reward_value: str
    min_order_amount: float
    is_active: bool


class StampCardSchema(BaseModel):
    """使用者集點卡 Schema"""
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    template_id: str
    stamps_collected: int
    is_completed: bool
    is_reward_claimed: bool
    completed_at: Optional[str] = None
    created_at: str
    template: StampCardTemplateSchema


class StartCardRequest(BaseModel):
    """開始集點請求"""
    template_id: str


class AddStampRequest(BaseModel):
    """蓋章請求"""
    order_id: str


class MessageResponse(BaseModel):
    """通用訊息回應"""
    message: str


# ==================== API 端點 ====================

@router.get("/templates", response_model=List[StampCardTemplateSchema])
async def list_templates(db: DbSession):
    """
    取得所有啟用中的集點卡模板（公開）
    """
    templates = db.query(StampCardTemplate).filter(
        StampCardTemplate.is_active == True
    ).all()

    return [
        StampCardTemplateSchema(
            id=t.id,
            name=t.name,
            description=t.description,
            stamps_required=t.stamps_required,
            reward_type=t.reward_type,
            reward_value=t.reward_value,
            min_order_amount=float(t.min_order_amount),
            is_active=t.is_active,
        )
        for t in templates
    ]


@router.get("/my", response_model=List[StampCardSchema])
async def get_my_stamp_cards(
    db: DbSession,
    current_user: CurrentUser
):
    """
    取得我的集點卡
    """
    cards = db.query(StampCard).filter(
        StampCard.user_id == current_user.id
    ).order_by(StampCard.created_at.desc()).all()

    return [
        StampCardSchema(
            id=c.id,
            user_id=c.user_id,
            template_id=c.template_id,
            stamps_collected=c.stamps_collected,
            is_completed=c.is_completed,
            is_reward_claimed=c.is_reward_claimed,
            completed_at=c.completed_at.isoformat() if c.completed_at else None,
            created_at=c.created_at.isoformat(),
            template=StampCardTemplateSchema(
                id=c.template.id,
                name=c.template.name,
                description=c.template.description,
                stamps_required=c.template.stamps_required,
                reward_type=c.template.reward_type,
                reward_value=c.template.reward_value,
                min_order_amount=float(c.template.min_order_amount),
                is_active=c.template.is_active,
            ),
        )
        for c in cards
    ]


@router.post("/start", response_model=StampCardSchema)
async def start_stamp_card(
    request: StartCardRequest,
    db: DbSession,
    current_user: CurrentUser
):
    """
    開始新的集點卡

    同一模板不可重複開啟未完成的集點卡
    """
    # 檢查模板是否存在且啟用
    template = db.query(StampCardTemplate).filter(
        StampCardTemplate.id == request.template_id,
        StampCardTemplate.is_active == True
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="集點卡模板不存在或已停用"
        )

    # 檢查是否已有未完成的同模板集點卡
    existing = db.query(StampCard).filter(
        StampCard.user_id == current_user.id,
        StampCard.template_id == request.template_id,
        StampCard.is_completed == False
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已有一張進行中的同類型集點卡"
        )

    # 建立新集點卡
    card = StampCard(
        user_id=current_user.id,
        template_id=request.template_id,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return StampCardSchema(
        id=card.id,
        user_id=card.user_id,
        template_id=card.template_id,
        stamps_collected=card.stamps_collected,
        is_completed=card.is_completed,
        is_reward_claimed=card.is_reward_claimed,
        completed_at=None,
        created_at=card.created_at.isoformat(),
        template=StampCardTemplateSchema(
            id=template.id,
            name=template.name,
            description=template.description,
            stamps_required=template.stamps_required,
            reward_type=template.reward_type,
            reward_value=template.reward_value,
            min_order_amount=float(template.min_order_amount),
            is_active=template.is_active,
        ),
    )


@router.post("/{card_id}/stamp", response_model=StampCardSchema)
async def add_stamp(
    card_id: str,
    request: AddStampRequest,
    db: DbSession,
    current_user: CurrentUser
):
    """
    蓋章

    根據訂單金額驗證是否達到最低消費門檻，自動判斷是否集滿
    """
    # 取得集點卡
    card = db.query(StampCard).filter(
        StampCard.id == card_id,
        StampCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="集點卡不存在"
        )

    if card.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此集點卡已集滿"
        )

    # 驗證訂單
    order = db.query(Order).filter(
        Order.id == request.order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )

    # 檢查最低消費門檻
    template = card.template
    if order.total < template.min_order_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"訂單金額未達最低消費門檻 NT${template.min_order_amount}"
        )

    # 蓋章
    card.stamps_collected += 1

    # 自動完成
    if card.stamps_collected >= template.stamps_required:
        card.is_completed = True
        card.completed_at = datetime.now()

    db.commit()
    db.refresh(card)

    return StampCardSchema(
        id=card.id,
        user_id=card.user_id,
        template_id=card.template_id,
        stamps_collected=card.stamps_collected,
        is_completed=card.is_completed,
        is_reward_claimed=card.is_reward_claimed,
        completed_at=card.completed_at.isoformat() if card.completed_at else None,
        created_at=card.created_at.isoformat(),
        template=StampCardTemplateSchema(
            id=template.id,
            name=template.name,
            description=template.description,
            stamps_required=template.stamps_required,
            reward_type=template.reward_type,
            reward_value=template.reward_value,
            min_order_amount=float(template.min_order_amount),
            is_active=template.is_active,
        ),
    )


@router.post("/{card_id}/claim", response_model=MessageResponse)
async def claim_reward(
    card_id: str,
    db: DbSession,
    current_user: CurrentUser
):
    """
    兌換獎勵

    集點卡需已集滿且尚未兌換
    """
    card = db.query(StampCard).filter(
        StampCard.id == card_id,
        StampCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="集點卡不存在"
        )

    if not card.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="集點卡尚未集滿"
        )

    if card.is_reward_claimed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="獎勵已兌換過"
        )

    # 標記已兌換
    card.is_reward_claimed = True
    db.commit()

    template = card.template
    reward_desc = {
        "coupon": "優惠券",
        "free_item": "免費商品",
        "points": "點數",
    }.get(template.reward_type, "獎勵")

    return MessageResponse(
        message=f"恭喜！已成功兌換{reward_desc}：{template.reward_value}"
    )
