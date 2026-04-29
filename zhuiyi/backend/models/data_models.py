"""
数据模型 - 定义统一的消息和人物数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class MessagePlatform(str, Enum):
    """消息来源平台"""
    WECHAT = "wechat"
    QQ = "qq"
    SMS = "sms"
    MANUAL = "manual"  # 手动输入
    FILE = "file"  # 文件导入


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    EMOJI = "emoji"
    FILE = "file"
    SYSTEM = "system"


@dataclass
class Message:
    """统一消息格式"""
    id: str
    timestamp: datetime
    sender: str
    content: str
    message_type: MessageType = MessageType.TEXT
    platform: MessagePlatform = MessagePlatform.MANUAL
    chat_name: Optional[str] = None  # 聊天对象/群名
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "content": self.content,
            "message_type": self.message_type.value,
            "platform": self.platform.value,
            "chat_name": self.chat_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            id=data.get("id", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else datetime.now(),
            sender=data.get("sender", ""),
            content=data.get("content", ""),
            message_type=MessageType(data.get("message_type", "text")),
            platform=MessagePlatform(data.get("platform", "manual")),
            chat_name=data.get("chat_name"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ChatSession:
    """聊天会话"""
    id: str
    name: str
    platform: MessagePlatform
    messages: List[Message] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def get_messages_by_sender(self, sender: str) -> List[Message]:
        return [m for m in self.messages if m.sender == sender]


@dataclass
class LanguageStyle:
    """语言风格特征"""
    avg_sentence_length: float = 0.0
    common_phrases: List[str] = field(default_factory=list)
    emoji_preferences: List[str] = field(default_factory=list)
    punctuation_habits: Dict[str, float] = field(default_factory=dict)
    formality_level: float = 0.5  # 0=非常随意, 1=非常正式
    humor_level: float = 0.5
    emotional_expression: str = "moderate"  # reserved/moderate/expressive
    reply_length_distribution: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "avg_sentence_length": self.avg_sentence_length,
            "common_phrases": self.common_phrases,
            "emoji_preferences": self.emoji_preferences,
            "punctuation_habits": self.punctuation_habits,
            "formality_level": self.formality_level,
            "humor_level": self.humor_level,
            "emotional_expression": self.emotional_expression,
            "reply_length_distribution": self.reply_length_distribution,
        }


@dataclass
class PersonalityTraits:
    """性格特征（大五人格）"""
    extraversion: float = 0.5  # 外向性
    agreeableness: float = 0.5  # 宜人性
    conscientiousness: float = 0.5  # 尽责性
    neuroticism: float = 0.5  # 神经质
    openness: float = 0.5  # 开放性

    def to_dict(self) -> Dict:
        return {
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "conscientiousness": self.conscientiousness,
            "neuroticism": self.neuroticism,
            "openness": self.openness,
        }


@dataclass
class InterestProfile:
    """兴趣爱好"""
    topics: List[str] = field(default_factory=list)
    expertise: List[str] = field(default_factory=list)
    opinions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "topics": self.topics,
            "expertise": self.expertise,
            "opinions": self.opinions,
        }


@dataclass
class CharacterProfile:
    """完整人物档案"""
    id: str
    name: str
    platform: MessagePlatform = MessagePlatform.MANUAL
    language_style: LanguageStyle = field(default_factory=LanguageStyle)
    personality: PersonalityTraits = field(default_factory=PersonalityTraits)
    interests: InterestProfile = field(default_factory=InterestProfile)
    total_messages: int = 0
    date_range: Optional[tuple] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform.value,
            "language_style": self.language_style.to_dict(),
            "personality": self.personality.to_dict(),
            "interests": self.interests.to_dict(),
            "total_messages": self.total_messages,
            "created_at": self.created_at.isoformat(),
        }
