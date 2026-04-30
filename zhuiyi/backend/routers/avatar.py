"""
数字人路由 - 数字人状态和头像管理
"""

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from services.avatar_service import AvatarService

router = APIRouter()

avatar_service = AvatarService()


@router.get("/{character_id}/state")
async def get_avatar_state(
    character_id: str,
    emotion: str = "neutral",
    is_speaking: bool = False,
):
    """获取数字人当前状态"""
    return avatar_service.get_avatar_state(
        character_id=character_id,
        emotion=emotion,
        is_speaking=is_speaking,
    )


@router.get("/{character_id}/config")
async def get_avatar_config(character_id: str):
    """获取数字人配置"""
    return avatar_service.get_avatar_config(character_id)


@router.post("/{character_id}/config")
async def update_avatar_config(character_id: str, config: dict):
    """更新数字人配置"""
    avatar_service.save_avatar_config(character_id, config)
    return {"status": "ok"}


@router.post("/{character_id}/image")
async def upload_avatar_image(
    character_id: str,
    image: UploadFile = File(...),
):
    """上传人物头像图片"""
    try:
        content = await image.read()
        path = avatar_service.save_avatar_image(
            character_id=character_id,
            image_data=content,
            filename=image.filename or "avatar.png",
        )
        return {"status": "ok", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}/image")
async def get_avatar_image(character_id: str):
    """获取人物头像图片"""
    config = avatar_service.get_avatar_config(character_id)
    image_path = config.get("image_path")
    if not image_path:
        raise HTTPException(status_code=404, detail="未设置头像")
    return FileResponse(image_path)


@router.get("/{character_id}/lip-sync")
async def get_lip_sync(character_id: str, text: str, duration: float = 1.0):
    """获取唇形同步数据"""
    return avatar_service.get_lip_sync_data(text=text, duration=duration)


@router.get("/expressions")
async def get_expressions():
    """获取可用表情列表"""
    return {"expressions": avatar_service.EXPRESSIONS}
