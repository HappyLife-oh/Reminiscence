"""
认证路由 - 用户注册、登录
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends

from auth import (
    UserCreate, UserLogin, Token, UserInfo,
    hash_password, verify_password, create_access_token,
    get_current_user,
)
from database import create_user, get_user_by_username

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    """用户注册"""
    if not user.username or len(user.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少3个字符")
    if not user.password or len(user.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6个字符")

    # 检查用户名是否已存在
    existing = get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    user_id = str(uuid.uuid4())[:8]
    create_user(user_id, user.username, hash_password(user.password))

    token = create_access_token(user_id, user.username)
    logger.info(f"用户注册成功: {user.username}")
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    """用户登录"""
    db_user = get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(db_user["id"], db_user["username"])
    logger.info(f"用户登录成功: {user.username}")
    return Token(access_token=token)


@router.get("/me", response_model=UserInfo)
async def get_me(user: UserInfo = Depends(get_current_user)):
    """获取当前用户信息"""
    if user is None:
        raise HTTPException(status_code=401, detail="未登录")
    return user
