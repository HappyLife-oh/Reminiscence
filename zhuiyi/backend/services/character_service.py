"""
人物管理服务 - 管理人物档案的存储和检索
"""

import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from models.data_models import (
    CharacterProfile, Message, MessagePlatform,
    LanguageStyle, PersonalityTraits, InterestProfile
)


# 数据存储目录
DATA_DIR = Path.home() / ".zhuiyi" / "characters"


class CharacterService:
    """人物管理服务"""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _get_character_dir(self, character_id: str) -> Path:
        char_dir = DATA_DIR / character_id
        char_dir.mkdir(parents=True, exist_ok=True)
        return char_dir

    def save_character(self, profile: CharacterProfile) -> str:
        """保存人物档案"""
        char_dir = self._get_character_dir(profile.id)

        # 保存档案
        profile_path = char_dir / "profile.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)

        return profile.id

    def load_character(self, character_id: str) -> Optional[CharacterProfile]:
        """加载人物档案"""
        char_dir = self._get_character_dir(character_id)
        profile_path = char_dir / "profile.json"

        if not profile_path.exists():
            return None

        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self._dict_to_profile(data)

    def list_characters(self) -> List[Dict]:
        """列出所有人物"""
        characters = []
        for char_dir in DATA_DIR.iterdir():
            if char_dir.is_dir():
                profile_path = char_dir / "profile.json"
                if profile_path.exists():
                    try:
                        with open(profile_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        characters.append({
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "total_messages": data.get("total_messages", 0),
                            "created_at": data.get("created_at"),
                        })
                    except (json.JSONDecodeError, IOError):
                        continue
        return characters

    def delete_character(self, character_id: str) -> bool:
        """删除人物档案"""
        import shutil
        char_dir = DATA_DIR / character_id
        if char_dir.exists():
            shutil.rmtree(char_dir)
            return True
        return False

    def save_messages(self, character_id: str, messages: List[Message]) -> int:
        """保存消息到人物的聊天记录中"""
        char_dir = self._get_character_dir(character_id)
        messages_path = char_dir / "messages.jsonl"

        # 追加模式写入
        with open(messages_path, "a", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + "\n")

        return len(messages)

    def load_messages(self, character_id: str) -> List[Message]:
        """加载人物的所有消息"""
        char_dir = self._get_character_dir(character_id)
        messages_path = char_dir / "messages.jsonl"

        if not messages_path.exists():
            return []

        messages = []
        with open(messages_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        messages.append(Message.from_dict(data))
                    except (json.JSONDecodeError, KeyError):
                        continue

        return messages

    def save_system_prompt(self, character_id: str, prompt: str):
        """保存生成的系统提示词"""
        char_dir = self._get_character_dir(character_id)
        prompt_path = char_dir / "system_prompt.txt"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

    def load_system_prompt(self, character_id: str) -> Optional[str]:
        """加载系统提示词"""
        char_dir = self._get_character_dir(character_id)
        prompt_path = char_dir / "system_prompt.txt"

        if not prompt_path.exists():
            return None

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _dict_to_profile(self, data: Dict) -> CharacterProfile:
        """将字典转换为CharacterProfile"""
        style_data = data.get("language_style", {})
        lang_style = LanguageStyle(
            avg_sentence_length=style_data.get("avg_sentence_length", 0),
            common_phrases=style_data.get("common_phrases", []),
            emoji_preferences=style_data.get("emoji_preferences", []),
            punctuation_habits=style_data.get("punctuation_habits", {}),
            formality_level=style_data.get("formality_level", 0.5),
            humor_level=style_data.get("humor_level", 0.5),
            emotional_expression=style_data.get("emotional_expression", "moderate"),
            reply_length_distribution=style_data.get("reply_length_distribution", {}),
        )

        pers_data = data.get("personality", {})
        personality = PersonalityTraits(
            extraversion=pers_data.get("extraversion", 0.5),
            agreeableness=pers_data.get("agreeableness", 0.5),
            conscientiousness=pers_data.get("conscientiousness", 0.5),
            neuroticism=pers_data.get("neuroticism", 0.5),
            openness=pers_data.get("openness", 0.5),
        )

        interest_data = data.get("interests", {})
        interests = InterestProfile(
            topics=interest_data.get("topics", []),
            expertise=interest_data.get("expertise", []),
            opinions=interest_data.get("opinions", {}),
        )

        return CharacterProfile(
            id=data.get("id", ""),
            name=data.get("name", ""),
            platform=MessagePlatform(data.get("platform", "manual")),
            language_style=lang_style,
            personality=personality,
            interests=interests,
            total_messages=data.get("total_messages", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
        )
