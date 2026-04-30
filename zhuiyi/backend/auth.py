"""
认证模块 - JWT Token认证
使用纯Python实现，无需SQLAlchemy
"""

import logging
import uuid
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 配置
SECRET_KEY = "zhuiyi-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)


class UserCreate(BaseModel):
    """用户注册"""
    username: str
    password: str


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """用户信息"""
    user_id: str
    username: str


def hash_password(password: str) -> str:
    """加密密码（使用SHA256+盐）"""
    salt = uuid.uuid4().hex[:16]
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        salt, hashed = hashed_password.split("$", 1)
        return hmac.compare_digest(
            hashed,
            hashlib.sha256((salt + plain_password).encode()).hexdigest()
        )
    except (ValueError, AttributeError):
        return False


def _base64url_encode(data: bytes) -> str:
    """Base64 URL编码"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _base64url_decode(s: str) -> bytes:
    """Base64 URL解码"""
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _sign(message: str) -> str:
    """HMAC-SHA256签名"""
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return _base64url_encode(signature)


def create_access_token(user_id: str, username: str) -> str:
    """创建JWT Token"""
    header = _base64url_encode(json.dumps({"alg": ALGORITHM, "typ": "JWT"}).encode())
    
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "username": username,
        "exp": int(expire.timestamp()),
    }
    payload_encoded = _base64url_encode(json.dumps(payload).encode())
    
    signature = _sign(f"{header}.{payload_encoded}")
    
    return f"{header}.{payload_encoded}.{signature}"


def decode_token(token: str) -> Optional[Dict]:
    """解码JWT Token"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header, payload, signature = parts
        
        # 验证签名
        expected_sig = _sign(f"{header}.{payload}")
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # 解码payload
        data = json.loads(_base64url_decode(payload))
        
        # 验证过期时间
        if data.get("exp", 0) < datetime.utcnow().timestamp():
            return None
        
        return data
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserInfo]:
    """获取当前用户（可选认证）"""
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials)
    if payload is None:
        return None

    return UserInfo(
        user_id=payload.get("sub", ""),
        username=payload.get("username", ""),
    )


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInfo:
    """要求认证"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )

    return UserInfo(
        user_id=payload.get("sub", ""),
        username=payload.get("username", ""),
    )
