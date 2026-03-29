"""
認證 API 路由

處理 LINE Login 認證和 Token 管理
"""
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUser
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["認證"])


class LineLoginRequest(BaseModel):
    """LINE Login 請求"""
    access_token: str


class LineLoginResponse(BaseModel):
    """LINE Login 回應"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """使用者資訊回應"""
    id: str
    line_user_id: str
    display_name: Optional[str]
    picture_url: Optional[str]
    phone: Optional[str]
    default_address: Optional[str]


class UpdateProfileRequest(BaseModel):
    """更新個人資料請求"""
    phone: Optional[str] = None
    default_address: Optional[str] = None


@router.post("/login", response_model=LineLoginResponse)
async def line_login(
    request: LineLoginRequest,
    db: DbSession
):
    """
    LINE Login 認證
    
    使用 LINE Access Token 驗證並建立系統 JWT Token
    
    Args:
        request: 包含 LINE Access Token 的請求
        db: 資料庫會話
        
    Returns:
        LineLoginResponse: 系統 JWT Token 和使用者資訊
    """
    # 向 LINE API 驗證 Token 並取得使用者資訊
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.line.me/v2/profile",
                headers={"Authorization": f"Bearer {request.access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="LINE Token 驗證失敗"
                )
            
            line_profile = response.json()
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="無法連線至 LINE 服務"
            )
    
    line_user_id = line_profile.get("userId")
    display_name = line_profile.get("displayName")
    picture_url = line_profile.get("pictureUrl")
    
    # 查詢或建立使用者
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    
    if not user:
        # 新使用者，建立帳號
        user = User(
            line_user_id=line_user_id,
            display_name=display_name,
            picture_url=picture_url
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # 既有使用者，更新資料
        user.display_name = display_name
        user.picture_url = picture_url
        db.commit()
        db.refresh(user)
    
    # 建立 JWT Token
    access_token = create_access_token(data={"sub": user.id})
    
    return LineLoginResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "line_user_id": user.line_user_id,
            "display_name": user.display_name,
            "picture_url": user.picture_url,
            "phone": user.phone,
            "default_address": user.default_address
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """
    取得當前使用者資訊
    
    Args:
        current_user: 當前登入使用者
        
    Returns:
        UserResponse: 使用者資訊
    """
    return UserResponse(
        id=current_user.id,
        line_user_id=current_user.line_user_id,
        display_name=current_user.display_name,
        picture_url=current_user.picture_url,
        phone=current_user.phone,
        default_address=current_user.default_address
    )


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: CurrentUser,
    db: DbSession
):
    """
    更新個人資料
    
    Args:
        request: 更新請求
        current_user: 當前登入使用者
        db: 資料庫會話
        
    Returns:
        UserResponse: 更新後的使用者資訊
    """
    if request.phone is not None:
        current_user.phone = request.phone
    
    if request.default_address is not None:
        current_user.default_address = request.default_address
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        line_user_id=current_user.line_user_id,
        display_name=current_user.display_name,
        picture_url=current_user.picture_url,
        phone=current_user.phone,
        default_address=current_user.default_address
    )
