"""
TTS服务 - 基于MiMo API的语音合成
支持：基础TTS、声音克隆、声音设计

MiMo支持的模型：
- MiMo-V2.5-TTS: 基础语音合成
- MiMo-V2.5-TTS-VoiceClone: 声音克隆
- MiMo-V2.5-TTS-VoiceDesign: 声音设计
- MiMo-V2-TTS: V2版本语音合成
"""

import httpx
import uuid
from pathlib import Path
from typing import Optional

from services.config_service import ConfigService, PROVIDERS


# 音频存储目录
AUDIO_DIR = Path.home() / ".zhuiyi" / "audio"


class TTSService:
    """TTS语音合成服务"""

    # MiMo TTS模型
    MODELS = {
        "tts": "MiMo-V2.5-TTS",
        "voice_clone": "MiMo-V2.5-TTS-VoiceClone",
        "voice_design": "MiMo-V2.5-TTS-VoiceDesign",
        "tts_v2": "MiMo-V2-TTS",
    }

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def _get_api_config(self) -> tuple[str, str]:
        """获取MiMo API配置"""
        config = self.config_service.get_provider_config("mimo")
        if not config or not config.get("api_key"):
            raise ValueError("未配置MiMo API密钥")

        provider_info = PROVIDERS.get("mimo", {})
        base_url = config.get("base_url", provider_info.get("base_url", ""))
        api_key = config.get("api_key", "")

        return base_url, api_key

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        model: str = "tts",
        output_path: Optional[str] = None,
    ) -> str:
        """
        文本转语音
        返回音频文件路径
        """
        base_url, api_key = self._get_api_config()
        model_name = self.MODELS.get(model, self.MODELS["tts"])

        # 构建请求
        request_body = {
            "model": model_name,
            "input": text,
            "voice": voice_id or "default",
            "speed": speed,
            "response_format": "mp3",
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(proxy=None, trust_env=False, timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/audio/speech",
                headers=headers,
                json=request_body,
            )

            if response.status_code != 200:
                raise Exception(f"TTS请求失败: {response.status_code} - {response.text}")

            # 保存音频文件
            if not output_path:
                filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
                output_path = str(AUDIO_DIR / filename)

            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path

    async def voice_clone(
        self,
        reference_audio_path: str,
        text: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        声音克隆 - 使用参考音频克隆声音
        返回音频文件路径
        """
        base_url, api_key = self._get_api_config()

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        # 读取参考音频
        with open(reference_audio_path, "rb") as f:
            audio_data = f.read()

        async with httpx.AsyncClient(proxy=None, trust_env=False, timeout=120.0) as client:
            files = {
                "audio": ("reference.mp3", audio_data, "audio/mpeg"),
            }
            data = {
                "model": self.MODELS["voice_clone"],
                "input": text,
                "response_format": "mp3",
            }

            response = await client.post(
                f"{base_url}/audio/voice-clone",
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code != 200:
                raise Exception(f"声音克隆请求失败: {response.status_code} - {response.text}")

            if not output_path:
                filename = f"clone_{uuid.uuid4().hex[:8]}.mp3"
                output_path = str(AUDIO_DIR / filename)

            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path

    async def voice_design(
        self,
        description: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        声音设计 - 根据描述生成声音
        返回音频文件路径
        """
        base_url, api_key = self._get_api_config()

        request_body = {
            "model": self.MODELS["voice_design"],
            "input": description,
            "response_format": "mp3",
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(proxy=None, trust_env=False, timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/audio/voice-design",
                headers=headers,
                json=request_body,
            )

            if response.status_code != 200:
                raise Exception(f"声音设计请求失败: {response.status_code} - {response.text}")

            if not output_path:
                filename = f"design_{uuid.uuid4().hex[:8]}.mp3"
                output_path = str(AUDIO_DIR / filename)

            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path

    def get_audio_path(self, filename: str) -> str:
        """获取音频文件路径"""
        return str(AUDIO_DIR / filename)
