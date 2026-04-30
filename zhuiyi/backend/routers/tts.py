"""
TTS路由 - 语音合成API
"""

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from services.tts_service import TTSService

router = APIRouter()


class TTSRequest(BaseModel):
    """TTS请求"""
    text: str
    voice_id: Optional[str] = None
    speed: Optional[float] = 1.0
    model: Optional[str] = "tts"


class VoiceCloneRequest(BaseModel):
    """声音克隆请求"""
    text: str


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-clone")
async def voice_clone(
    request: Request,
    audio: UploadFile = File(...),
    text: str = Form(...),
):
    """声音克隆"""
    try:
        tts_service = TTSService(request.app.state.config_service)

        # 保存上传的参考音频
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            audio_path = await tts_service.voice_clone(
                reference_audio_path=tmp_path,
                text=text,
            )
            return FileResponse(
                audio_path,
                media_type="audio/mpeg",
                filename="cloned_speech.mp3",
            )
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-design")
async def voice_design(request: Request, description: str = Form(...)):
    """声音设计"""
    try:
        tts_service = TTSService(request.app.state.config_service)
        audio_path = await tts_service.voice_design(description=description)
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename="designed_voice.mp3",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
