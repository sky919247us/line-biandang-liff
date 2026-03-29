"""
安全性模組

提供 JWT Token 生成與驗證、密碼雜湊等功能
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# 密碼雜湊上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 設定
ALGORITHM = "HS256"


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    建立 JWT Access Token
    
    Args:
        data: Token 內容資料
        expires_delta: 過期時間差，預設使用設定值
        
    Returns:
        str: JWT Token 字串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    驗證 JWT Token
    
    Args:
        token: JWT Token 字串
        
    Returns:
        dict | None: Token 內容資料，驗證失敗時回傳 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證密碼
    
    Args:
        plain_password: 明文密碼
        hashed_password: 已雜湊的密碼
        
    Returns:
        bool: 密碼是否正確
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    對密碼進行雜湊
    
    Args:
        password: 明文密碼
        
    Returns:
        str: 雜湊後的密碼
    """
    return pwd_context.hash(password)
