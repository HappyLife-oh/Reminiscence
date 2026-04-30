"""
数字人服务 - 轻量级实现
使用图片+CSS动画实现数字人效果，无需GPU
支持：静态头像、表情动画、唇形同步
"""

import uuid
from pathlib import Path
from typing import Optional, Dict, List

from services.character_service import CharacterService


# 头像存储目录
AVATAR_DIR = Path.home() / ".zhuiyi" / "avatars"


class AvatarService:
    """数字人服务 - 轻量级实现"""

    # 预设表情
    EXPRESSIONS = {
        "neutral": {"emoji": "😐", "description": "平静"},
        "happy": {"emoji": "😊", "description": "开心"},
        "sad": {"emoji": "😢", "description": "难过"},
        "angry": {"emoji": "😤", "description": "生气"},
        "surprised": {"emoji": "😲", "description": "惊讶"},
        "thinking": {"emoji": "🤔", "description": "思考"},
        "laughing": {"emoji": "😂", "description": "大笑"},
        "love": {"emoji": "🥰", "description": "喜爱"},
    }

    def __init__(self):
        AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    def get_avatar_config(self, character_id: str) -> Dict:
        """获取人物的数字人配置"""
        avatar_dir = AVATAR_DIR / character_id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        config_path = avatar_dir / "config.json"
        if config_path.exists():
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # 默认配置
        return {
            "character_id": character_id,
            "avatar_type": "emoji",  # emoji / image / animated
            "default_expression": "neutral",
            "has_custom_image": False,
            "animations_enabled": True,
        }

    def save_avatar_config(self, character_id: str, config: Dict):
        """保存数字人配置"""
        avatar_dir = AVATAR_DIR / character_id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        import json
        config_path = avatar_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def save_avatar_image(self, character_id: str, image_data: bytes, filename: str) -> str:
        """保存人物头像图片"""
        avatar_dir = AVATAR_DIR / character_id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # 保存图片
        image_path = avatar_dir / f"avatar{Path(filename).suffix}"
        with open(image_path, "wb") as f:
            f.write(image_data)

        # 更新配置
        config = self.get_avatar_config(character_id)
        config["avatar_type"] = "image"
        config["has_custom_image"] = True
        config["image_path"] = str(image_path)
        self.save_avatar_config(character_id, config)

        return str(image_path)

    def get_expression_for_emotion(self, emotion: str) -> Dict:
        """根据情感状态获取表情"""
        emotion_to_expression = {
            "joy": "happy",
            "sadness": "sad",
            "anger": "angry",
            "surprise": "surprised",
            "neutral": "neutral",
        }
        expression_key = emotion_to_expression.get(emotion, "neutral")
        return self.EXPRESSIONS.get(expression_key, self.EXPRESSIONS["neutral"])

    def get_lip_sync_data(self, text: str, duration: float = 1.0) -> List[Dict]:
        """
        生成简单的唇形同步数据
        基于文本长度估算音素时间
        """
        # 简化实现：基于字符数估算
        char_count = len(text)
        if char_count == 0:
            return []

        # 每个字符大约0.15秒
        char_duration = 0.15
        total_duration = char_count * char_duration

        # 生成音素序列
        phonemes = []
        for i, char in enumerate(text):
            if char in "aeiouaeiouü":
                phonemes.append({
                    "time": i * char_duration,
                    "mouth": "open",
                    "intensity": 0.8,
                })
            elif char in "bpmfdtnlgkhjqxzcsryw":
                phonemes.append({
                    "time": i * char_duration,
                    "mouth": "closed",
                    "intensity": 0.3,
                })
            elif char in "，。！？、":
                phonemes.append({
                    "time": i * char_duration,
                    "mouth": "pause",
                    "intensity": 0.0,
                })
            else:
                phonemes.append({
                    "time": i * char_duration,
                    "mouth": "neutral",
                    "intensity": 0.5,
                })

        return phonemes

    def get_avatar_state(self, character_id: str, emotion: str = "neutral", is_speaking: bool = False) -> Dict:
        """获取数字人当前状态"""
        config = self.get_avatar_config(character_id)
        expression = self.get_expression_for_emotion(emotion)

        return {
            "character_id": character_id,
            "avatar_type": config.get("avatar_type", "emoji"),
            "expression": expression,
            "is_speaking": is_speaking,
            "has_custom_image": config.get("has_custom_image", False),
            "image_path": config.get("image_path"),
            "animations_enabled": config.get("animations_enabled", True),
        }
