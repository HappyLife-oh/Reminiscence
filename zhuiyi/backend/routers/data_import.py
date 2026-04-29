"""
数据导入路由 - 处理数据上传和特征提取
"""

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json

from models.data_models import MessagePlatform
from services.data_parser import auto_parse, get_parser
from services.feature_extractor import FeatureExtractor
from services.character_service import CharacterService

router = APIRouter()

# 初始化服务
feature_extractor = FeatureExtractor()
character_service = CharacterService()


class PasteImportRequest(BaseModel):
    """粘贴文本导入请求"""
    content: str
    character_name: str
    platform: Optional[str] = "manual"
    chat_name: Optional[str] = ""


class CharacterResponse(BaseModel):
    """人物档案响应"""
    id: str
    name: str
    total_messages: int
    language_style: dict
    personality: dict
    interests: dict
    system_prompt: Optional[str] = None


@router.post("/import/text")
async def import_text(
    content: str = Form(...),
    character_name: str = Form(...),
    file_type: str = Form("auto"),
    platform: str = Form("manual"),
    chat_name: str = Form(""),
):
    """
    导入文本数据（粘贴或上传文本内容）
    支持：TXT、CSV、JSON、自动检测
    """
    try:
        # 解析消息
        msg_platform = MessagePlatform(platform)
        messages = auto_parse(
            content,
            file_type=file_type if file_type != "auto" else None,
            platform=msg_platform,
            chat_name=chat_name,
        )

        if not messages:
            raise HTTPException(status_code=400, detail="未能解析出任何消息，请检查数据格式")

        # 创建人物档案
        profile = feature_extractor.extract_character_profile(
            messages=messages,
            character_name=character_name,
        )

        # 保存人物档案
        character_id = character_service.save_character(profile)

        # 保存消息
        character_service.save_messages(character_id, messages)

        # 生成并保存系统提示词
        system_prompt = feature_extractor.generate_system_prompt(profile)
        character_service.save_system_prompt(character_id, system_prompt)

        return {
            "status": "ok",
            "character_id": character_id,
            "character_name": character_name,
            "message_count": len(messages),
            "profile": profile.to_dict(),
            "system_prompt": system_prompt,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/file")
async def import_file(
    file: UploadFile = File(...),
    character_name: str = Form(...),
    file_type: str = Form("auto"),
    platform: str = Form("manual"),
    chat_name: str = Form(""),
):
    """
    导入文件数据
    支持：.txt, .csv, .json
    """
    # 检查文件类型
    allowed_extensions = {".txt", ".csv", ".json", ".log"}
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，支持: {', '.join(allowed_extensions)}"
        )

    try:
        # 读取文件内容
        content = await file.read()

        # 自动检测编码
        import chardet
        detected = chardet.detect(content)
        encoding = detected.get("encoding", "utf-8")

        try:
            text_content = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text_content = content.decode("utf-8", errors="replace")

        # 确定文件类型
        if file_type == "auto":
            type_map = {".txt": "txt", ".csv": "csv", ".json": "json", ".log": "txt"}
            file_type = type_map.get(file_ext, "txt")

        # 解析消息
        msg_platform = MessagePlatform(platform)
        parser = get_parser(file_type)
        messages = parser.parse(text_content, platform=msg_platform, chat_name=chat_name)

        if not messages:
            raise HTTPException(status_code=400, detail="未能从文件中解析出任何消息")

        # 创建人物档案
        profile = feature_extractor.extract_character_profile(
            messages=messages,
            character_name=character_name,
        )

        # 保存
        character_id = character_service.save_character(profile)
        character_service.save_messages(character_id, messages)
        system_prompt = feature_extractor.generate_system_prompt(profile)
        character_service.save_system_prompt(character_id, system_prompt)

        return {
            "status": "ok",
            "character_id": character_id,
            "character_name": character_name,
            "message_count": len(messages),
            "profile": profile.to_dict(),
            "system_prompt": system_prompt,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/characters")
async def list_characters():
    """列出所有人物"""
    return character_service.list_characters()


@router.get("/characters/{character_id}")
async def get_character(character_id: str):
    """获取人物详情"""
    profile = character_service.load_character(character_id)
    if not profile:
        raise HTTPException(status_code=404, detail="人物不存在")

    system_prompt = character_service.load_system_prompt(character_id)
    messages = character_service.load_messages(character_id)

    return {
        "profile": profile.to_dict(),
        "system_prompt": system_prompt,
        "message_count": len(messages),
    }


@router.get("/characters/{character_id}/prompt")
async def get_character_prompt(character_id: str):
    """获取人物的系统提示词"""
    prompt = character_service.load_system_prompt(character_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="人物不存在或未生成提示词")
    return {"character_id": character_id, "system_prompt": prompt}


@router.delete("/characters/{character_id}")
async def delete_character(character_id: str):
    """删除人物"""
    success = character_service.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="人物不存在")
    return {"status": "ok", "message": "已删除"}
