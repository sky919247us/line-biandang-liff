"""
推薦好友 API 路由

處理推薦碼產生、推薦紀錄查詢、推薦碼套用與完成推薦
"""
import logging
import string
import random
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUser
from app.models.referral import Referral


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/referrals", tags=["推薦好友"])


# ── Request / Response Schemas ──────────────────────────────────────


class ApplyCodeRequest(BaseModel):
    """套用推薦碼請求"""
    code: str


class ReferralCodeResponse(BaseModel):
    """推薦碼回應"""
    referral_code: str
    share_link: str


class ReferredUserResponse(BaseModel):
    """被推薦人資訊"""
    id: str
    referred_name: Optional[str]
    status: str
    referrer_reward_type: Optional[str]
    referrer_reward_value: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class MyReferralsResponse(BaseModel):
    """我的推薦紀錄回應"""
    total: int
    completed: int
    rewarded: int
    referrals: List[ReferredUserResponse]


class ReferralResultResponse(BaseModel):
    """推薦操作結果回應"""
    message: str
    referral_id: str
    status: str


class CompleteResultResponse(BaseModel):
    """完成推薦結果回應"""
    message: str
    referral_id: str
    status: str
    referrer_reward_type: Optional[str]
    referrer_reward_value: Optional[str]
    referred_reward_type: Optional[str]
    referred_reward_value: Optional[str]


# ── Helper ──────────────────────────────────────────────────────────


def _generate_referral_code() -> str:
    """產生隨機推薦碼 REF-XXXXXX"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=6))
    return f"REF-{random_part}"


# ── Routes ──────────────────────────────────────────────────────────


@router.get("/my-code", response_model=ReferralCodeResponse)
async def get_my_referral_code(
    current_user: CurrentUser,
    db: DbSession
):
    """
    取得或產生我的推薦碼

    若使用者已有推薦碼則回傳，否則產生新的推薦碼

    Args:
        current_user: 當前使用者
        db: 資料庫會話

    Returns:
        ReferralCodeResponse: 推薦碼與分享連結
    """
    # 查詢使用者是否已有推薦碼（以推薦人身份建立的紀錄）
    existing = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).first()

    if existing:
        code = existing.referral_code
    else:
        # 產生唯一推薦碼
        for _ in range(10):
            code = _generate_referral_code()
            conflict = db.query(Referral).filter(
                Referral.referral_code == code
            ).first()
            if not conflict:
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="無法產生唯一推薦碼，請稍後再試"
            )

        # 建立一筆佔位紀錄，referrer_id 等於 referred_id 表示尚無被推薦人
        placeholder = Referral(
            referrer_id=current_user.id,
            referred_id=current_user.id,
            referral_code=code,
            status="pending"
        )
        db.add(placeholder)
        db.commit()

    share_link = f"https://liff.line.me/?referral={code}"

    return ReferralCodeResponse(
        referral_code=code,
        share_link=share_link
    )


@router.get("/my-referrals", response_model=MyReferralsResponse)
async def get_my_referrals(
    current_user: CurrentUser,
    db: DbSession
):
    """
    取得我的推薦紀錄

    列出所有我推薦的使用者及其狀態

    Args:
        current_user: 當前使用者
        db: 資料庫會話

    Returns:
        MyReferralsResponse: 推薦紀錄列表與統計
    """
    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id,
        Referral.referred_id != current_user.id  # 排除佔位紀錄
    ).order_by(Referral.created_at.desc()).all()

    total = len(referrals)
    completed = sum(1 for r in referrals if r.status in ("completed", "rewarded"))
    rewarded = sum(1 for r in referrals if r.status == "rewarded")

    items = []
    for r in referrals:
        referred_name = r.referred.display_name if r.referred else None
        items.append(ReferredUserResponse(
            id=r.id,
            referred_name=referred_name,
            status=r.status,
            referrer_reward_type=r.referrer_reward_type,
            referrer_reward_value=r.referrer_reward_value,
            created_at=r.created_at,
            completed_at=r.completed_at,
        ))

    return MyReferralsResponse(
        total=total,
        completed=completed,
        rewarded=rewarded,
        referrals=items
    )


@router.post("/apply", response_model=ReferralResultResponse)
async def apply_referral_code(
    request: ApplyCodeRequest,
    current_user: CurrentUser,
    db: DbSession
):
    """
    套用推薦碼

    被推薦人輸入推薦碼，建立推薦關係

    Args:
        request: 包含推薦碼的請求
        current_user: 當前使用者（被推薦人）
        db: 資料庫會話

    Returns:
        ReferralResultResponse: 套用結果
    """
    code = request.code.strip().upper()

    # 查詢推薦碼是否存在
    referral_record = db.query(Referral).filter(
        Referral.referral_code == code
    ).first()

    if not referral_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推薦碼不存在"
        )

    # 不可自我推薦
    if referral_record.referrer_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不可使用自己的推薦碼"
        )

    # 檢查是否已經被推薦過
    already_referred = db.query(Referral).filter(
        Referral.referred_id == current_user.id,
        Referral.referrer_id != current_user.id  # 排除佔位紀錄
    ).first()

    if already_referred:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已使用過推薦碼"
        )

    # 建立新的推薦紀錄
    new_referral = Referral(
        referrer_id=referral_record.referrer_id,
        referred_id=current_user.id,
        referral_code=_generate_referral_code(),  # 新紀錄用新碼
        status="pending"
    )
    db.add(new_referral)
    db.commit()
    db.refresh(new_referral)

    logger.info(
        "推薦碼套用成功: referrer=%s, referred=%s",
        referral_record.referrer_id,
        current_user.id
    )

    return ReferralResultResponse(
        message="推薦碼套用成功",
        referral_id=new_referral.id,
        status=new_referral.status
    )


@router.post("/{referral_id}/complete", response_model=CompleteResultResponse)
async def complete_referral(
    referral_id: str,
    current_user: CurrentUser,
    db: DbSession
):
    """
    完成推薦（被推薦人完成首筆訂單後呼叫）

    將推薦狀態更新為 rewarded 並發放雙方獎勵

    Args:
        referral_id: 推薦紀錄 ID
        current_user: 當前使用者
        db: 資料庫會話

    Returns:
        CompleteResultResponse: 完成結果與獎勵資訊
    """
    referral = db.query(Referral).filter(
        Referral.id == referral_id
    ).first()

    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推薦紀錄不存在"
        )

    if referral.status == "rewarded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此推薦已完成獎勵發放"
        )

    if referral.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此推薦已完成"
        )

    # 預設獎勵：推薦人與被推薦人各獲得 50 點
    referrer_reward_type = "points"
    referrer_reward_value = "50"
    referred_reward_type = "points"
    referred_reward_value = "50"

    # 更新推薦紀錄
    referral.status = "rewarded"
    referral.completed_at = datetime.utcnow()
    referral.referrer_reward_type = referrer_reward_type
    referral.referrer_reward_value = referrer_reward_value
    referral.referred_reward_type = referred_reward_type
    referral.referred_reward_value = referred_reward_value

    db.commit()
    db.refresh(referral)

    logger.info(
        "推薦完成: id=%s, referrer=%s, referred=%s",
        referral.id,
        referral.referrer_id,
        referral.referred_id
    )

    return CompleteResultResponse(
        message="推薦獎勵已發放",
        referral_id=referral.id,
        status=referral.status,
        referrer_reward_type=referral.referrer_reward_type,
        referrer_reward_value=referral.referrer_reward_value,
        referred_reward_type=referral.referred_reward_type,
        referred_reward_value=referral.referred_reward_value,
    )
