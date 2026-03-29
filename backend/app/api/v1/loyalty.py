"""
會員點數 API 路由

處理點數帳戶查詢、交易紀錄和點數兌換
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, field_validator

from app.api.deps import DbSession, CurrentUser
from app.services.loyalty_service import LoyaltyService


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/loyalty", tags=["會員點數"])


# ── Request / Response Schemas ──────────────────────────────────────


class RedeemRequest(BaseModel):
    """點數兌換請求"""
    points: int

    @field_validator("points")
    @classmethod
    def points_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("兌換點數必須大於 0")
        return v


class LoyaltyAccountResponse(BaseModel):
    """點數帳戶回應"""
    id: str
    user_id: str
    balance: int
    total_earned: int
    total_redeemed: int
    tier: str
    created_at: datetime
    updated_at: datetime


class PointTransactionResponse(BaseModel):
    """點數交易紀錄回應"""
    id: str
    transaction_type: str
    points: int
    order_id: Optional[str]
    description: Optional[str]
    created_at: datetime


class TransactionListResponse(BaseModel):
    """點數交易紀錄列表回應"""
    items: List[PointTransactionResponse]
    total: int


class RedeemResponse(BaseModel):
    """點數兌換回應"""
    message: str
    points_redeemed: int
    discount_amount: int
    remaining_balance: int


# ── Routes ──────────────────────────────────────────────────────────


loyalty_service = LoyaltyService()


@router.get("/account", response_model=LoyaltyAccountResponse)
async def get_loyalty_account(
    current_user: CurrentUser,
    db: DbSession
):
    """
    取得會員點數帳戶

    若帳戶不存在，將自動建立

    Args:
        current_user: 當前使用者
        db: 資料庫會話

    Returns:
        LoyaltyAccountResponse: 點數帳戶資訊
    """
    account = loyalty_service.get_or_create_account(db, current_user.id)

    return LoyaltyAccountResponse(
        id=account.id,
        user_id=account.user_id,
        balance=account.points_balance,
        total_earned=account.total_earned,
        total_redeemed=account.total_redeemed,
        tier=account.tier,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    取得點數交易紀錄

    Args:
        current_user: 當前使用者
        db: 資料庫會話
        skip: 分頁偏移量
        limit: 取得數量

    Returns:
        TransactionListResponse: 交易紀錄列表
    """
    account = loyalty_service.get_or_create_account(db, current_user.id)

    transactions = loyalty_service.get_transactions(
        db, current_user.id, skip=skip, limit=limit
    )

    # 取得總筆數
    from app.models.loyalty import PointTransaction
    total = db.query(PointTransaction).filter(
        PointTransaction.loyalty_account_id == account.id
    ).count()

    items = [
        PointTransactionResponse(
            id=t.id,
            transaction_type=t.transaction_type,
            points=t.points,
            order_id=t.order_id,
            description=t.description,
            created_at=t.created_at
        )
        for t in transactions
    ]

    return TransactionListResponse(items=items, total=total)


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_points(
    request: RedeemRequest,
    current_user: CurrentUser,
    db: DbSession
):
    """
    兌換點數折扣

    1 點 = NT$1 折扣

    Args:
        request: 兌換請求（包含兌換點數）
        current_user: 當前使用者
        db: 資料庫會話

    Returns:
        RedeemResponse: 兌換結果
    """
    try:
        transaction = loyalty_service.redeem_points(
            db, current_user.id, request.points
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 取得更新後餘額
    balance = loyalty_service.get_balance(db, current_user.id)

    return RedeemResponse(
        message="點數兌換成功",
        points_redeemed=request.points,
        discount_amount=request.points,  # 1 點 = NT$1
        remaining_balance=balance
    )
