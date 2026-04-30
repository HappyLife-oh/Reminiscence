"""
TTS路由 - 语音合成API
"""

import logging
import os
import tempfile
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional

from services.tts_service import TTSService

logger = logging.getLogger(__name__)
router = APIRouter()


class TTSRequest(BaseModel):
    """TTS请求"""
    text: str
    voice_id: Optional[str] = None
    speed: Optional[float] = 1.0
    model: Optional[str] = "tts"

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("text不能为空")
        if len(v) > 5000:
            raise ValueError("text长度不能超过5000字符")
        return v

    @field_validator("speed")
    @classmethod
    def validate_speed(cls, v):
        if v is not None and (v < 0.5 or v > 2.0):
            raise ValueError("speed必须在0.5-2.0之间")
        return v


@router.post("/synthesize")
async def synthesize_speech(request: Request, tts_request: TTSRequest):
    """文本转语音"""
    try:
        tts_service = TTSService(request.app.state.config_service)
        audio_path = await tts_service.text_to_speech(
            text=tts_request.text,
            voice_id=tts_request.voice_id,
            speed=tts_request.speed,
            model=tts_request.model,
        )
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename="speech.mp3",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TTS合成失败: {e}")
        raise HTTPException(status_code=500, detail="语音合成失败，请稍后重试")


@router.post("/voice-clone")
async def voice_clone(
    request: Request,
    audio: UploadFile = File(...),
    text: str = Form(...),
):
    """声音克隆"""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text不能为空")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="text长度不能超过5000字符")

    # 检查音频文件大小（最大10MB）
    content = await audio.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="音频文件大小不能超过10MB")

    tmp_path = None
    try:
        tts_service = TTSService(request.app.state.config_service)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        audio_path = await tts_service.voice_clone(
            reference_audio_path=tmp_path,
            text=text,
        )
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename="cloned_speech.mp3",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"声音克隆失败: {e}")
        raise HTTPException(status_code=500, detail="声音克隆失败，请稍后重试")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/voice-design")
async def voice_design(request: Request, description: str = Form(...)):
    """声音设计"""
    if not description or not description.strip():
        raise HTTPException(status_code=400, detail="description不能为空")
    if len(description) > 1000:
        raise HTTPException(status_code=400, detail="description长度不能超过1000字符")

    try:
        tts_service = TTSService(request.app.state.config_service)
        audio_path = await tts_service.voice_design(description=description)
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename="designed_voice.mp3",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"声音设计失败: {e}")
        raise HTTPException(status_code=500, detail="声音设计失败，请稍后重试")


@router.get("/models")
async def get_tts_models():
    """获取可用的TTS模型列表"""
    return {
        "models": [
            {"key": "tts", "name": "MiMo-V2.5-TTS", "description": "基础语音合成"},
            {"key": "voice_clone", "name": "MiMo-V2.5-TTS-VoiceClone", "description": "声音克隆"},
            {"key": "voice_design", "name": "MiMo-V2.5-TTS-VoiceDesign", "description": "声音设计"},
            {"key": "tts_v2", "name": "MiMo-V2-TTS", "description": "V2版本语音合成"},
        ]
    }
