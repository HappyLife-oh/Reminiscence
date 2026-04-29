"""
特征提取服务 - 从聊天记录中提取人格特征
"""

import re
import json
from collections import Counter
from typing import List, Dict, Tuple
from datetime import datetime

import jieba
import jieba.analyse
from snownlp import SnowNLP

from models.data_models import (
    Message, LanguageStyle, PersonalityTraits,
    InterestProfile, CharacterProfile
)


class FeatureExtractor:
    """特征提取器"""

    # 停用词
    STOP_WORDS = set([
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
        "吗", "吧", "啊", "呢", "嗯", "哦", "哈", "呀", "额",
        "the", "a", "an", "is", "are", "was", "were", "be",
    ])

    # 表情符号正则
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        flags=re.UNICODE,
    )

    # 幽默/情感关键词
    HUMOR_KEYWORDS = set(["哈哈", "笑死", "绝了", "离谱", "搞笑", "逗", "lol", "haha", "233"])
    FORMAL_KEYWORDS = set(["您好", "请问", "谢谢", "不好意思", "麻烦", "请", "劳驾"])
    EMOTIONAL_KEYWORDS = set(["开心", "难过", "生气", "害怕", "惊喜", "感动", "伤心", "愤怒", "兴奋"])

    def extract_language_style(self, messages: List[Message]) -> LanguageStyle:
        """提取语言风格特征"""
        style = LanguageStyle()

        if not messages:
            return style

        # 只分析文本消息
        text_messages = [m for m in messages if m.content and len(m.content.strip()) > 0]
        if not text_messages:
            return style

        # 1. 平均句子长度
        lengths = [len(m.content) for m in text_messages]
        style.avg_sentence_length = sum(lengths) / len(lengths)

        # 2. 常用短语/口头禅
        all_phrases = []
        for msg in text_messages:
            # 提取2-4字的高频短语
            words = jieba.lcut(msg.content)
            for i in range(len(words)):
                for n in range(2, min(5, len(words) - i + 1)):
                    phrase = "".join(words[i:i+n])
                    if len(phrase) >= 2 and phrase not in self.STOP_WORDS:
                        all_phrases.append(phrase)

        phrase_counter = Counter(all_phrases)
        # 过滤出现次数太少的
        style.common_phrases = [
            phrase for phrase, count in phrase_counter.most_common(30)
            if count >= 3
        ][:15]

        # 3. 表情偏好
        all_emojis = []
        for msg in text_messages:
            emojis = self.EMOJI_PATTERN.findall(msg.content)
            all_emojis.extend(emojis)
        emoji_counter = Counter(all_emojis)
        style.emoji_preferences = [e for e, _ in emoji_counter.most_common(10)]

        # 4. 标点习惯
        punctuation_counts = {
            "exclamation": 0,  # 感叹号
            "question": 0,     # 问号
            "ellipsis": 0,     # 省略号
            "period": 0,       # 句号
        }
        for msg in text_messages:
            punctuation_counts["exclamation"] += msg.content.count("！") + msg.content.count("!")
            punctuation_counts["question"] += msg.content.count("？") + msg.content.count("?")
            punctuation_counts["ellipsis"] += msg.content.count("…") + msg.content.count("...")
            punctuation_counts["period"] += msg.content.count("。")

        total_punct = sum(punctuation_counts.values()) or 1
        style.punctuation_habits = {
            k: round(v / total_punct, 3) for k, v in punctuation_counts.items()
        }

        # 5. 正式程度
        formal_count = sum(1 for m in text_messages if any(w in m.content for w in self.FORMAL_KEYWORDS))
        style.formality_level = round(formal_count / len(text_messages), 3)

        # 6. 幽默程度
        humor_count = sum(1 for m in text_messages if any(w in m.content for w in self.HUMOR_KEYWORDS))
        style.humor_level = round(humor_count / len(text_messages), 3)

        # 7. 情感表达程度
        emotional_count = sum(1 for m in text_messages if any(w in m.content for w in self.EMOTIONAL_KEYWORDS))
        emotional_ratio = emotional_count / len(text_messages)
        if emotional_ratio > 0.1:
            style.emotional_expression = "expressive"
        elif emotional_ratio > 0.03:
            style.emotional_expression = "moderate"
        else:
            style.emotional_expression = "reserved"

        # 8. 回复长度分布
        short = sum(1 for l in lengths if l <= 5)
        medium = sum(1 for l in lengths if 5 < l <= 20)
        long_ = sum(1 for l in lengths if l > 20)
        total = len(lengths)
        style.reply_length_distribution = {
            "short": round(short / total, 3),
            "medium": round(medium / total, 3),
            "long": round(long_ / total, 3),
        }

        return style

    def extract_personality(self, messages: List[Message]) -> PersonalityTraits:
        """提取性格特征（基于文本分析的简化版本）"""
        personality = PersonalityTraits()

        if not messages:
            return personality

        text_messages = [m for m in messages if m.content]
        if not text_messages:
            return personality

        # 外向性：消息频率、使用感叹号和表情的频率
        emoji_count = sum(len(self.EMOJI_PATTERN.findall(m.content)) for m in text_messages)
        exclamation_count = sum(m.content.count("！") + m.content.count("!") for m in text_messages)
        personality.extraversion = min(1.0, (emoji_count + exclamation_count) / len(text_messages) * 2)

        # 宜人性：正面词汇比例
        positive_words = set(["好的", "可以", "没问题", "谢谢", "辛苦", "棒", "好", "行", "嗯嗯"])
        positive_count = sum(1 for m in text_messages if any(w in m.content for w in positive_words))
        personality.agreeableness = min(1.0, positive_count / len(text_messages) * 3)

        # 尽责性：平均消息长度（较长的消息可能更认真）
        avg_len = sum(len(m.content) for m in text_messages) / len(text_messages)
        personality.conscientiousness = min(1.0, avg_len / 50)

        # 神经质：负面词汇比例
        negative_words = set(["烦", "累", "难过", "生气", "讨厌", "不想", "算了", "无所谓", "随便"])
        negative_count = sum(1 for m in text_messages if any(w in m.content for w in negative_words))
        personality.neuroticism = min(1.0, negative_count / len(text_messages) * 3)

        # 开放性：使用问号的比例（好奇心）
        question_count = sum(m.content.count("？") + m.content.count("?") for m in text_messages)
        personality.openness = min(1.0, question_count / len(text_messages) * 2)

        return personality

    def extract_interests(self, messages: List[Message]) -> InterestProfile:
        """提取兴趣爱好"""
        interests = InterestProfile()

        if not messages:
            return interests

        # 合并所有文本
        all_text = " ".join(m.content for m in messages if m.content)

        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(all_text, topK=30, withWeight=True)

        # 过滤和分类
        topic_keywords = []
        for word, weight in keywords:
            if len(word) >= 2 and word not in self.STOP_WORDS:
                topic_keywords.append(word)

        interests.topics = topic_keywords[:15]

        # 提取观点（包含"喜欢"、"讨厌"、"觉得"等词的句子）
        opinion_patterns = [
            (re.compile(r"喜欢(.{1,20})"), "喜欢"),
            (re.compile(r"讨厌(.{1,20})"), "讨厌"),
            (re.compile(r"觉得(.{1,20})"), "觉得"),
            (re.compile(r"最爱(.{1,20})"), "最爱"),
            (re.compile(r"不喜欢(.{1,20})"), "不喜欢"),
        ]

        for msg in messages:
            if not msg.content:
                continue
            for pattern, label in opinion_patterns:
                matches = pattern.findall(msg.content)
                for match in matches:
                    match = match.strip("，。！？,.!? ")
                    if match and len(match) <= 20:
                        interests.opinions[match] = label

        return interests

    def extract_character_profile(
        self,
        messages: List[Message],
        character_name: str,
        character_id: str = None,
    ) -> CharacterProfile:
        """提取完整人物档案"""
        if not character_id:
            character_id = f"char_{character_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        profile = CharacterProfile(
            id=character_id,
            name=character_name,
        )

        if not messages:
            return profile

        profile.total_messages = len(messages)

        # 提取各项特征
        profile.language_style = self.extract_language_style(messages)
        profile.personality = self.extract_personality(messages)
        profile.interests = self.extract_interests(messages)

        # 日期范围
        timestamps = [m.timestamp for m in messages if m.timestamp]
        if timestamps:
            profile.date_range = (min(timestamps), max(timestamps))

        return profile

    def generate_system_prompt(self, profile: CharacterProfile) -> str:
        """根据人物档案生成系统提示词"""
        style = profile.language_style
        personality = profile.personality
        interests = profile.interests

        # 构建性格描述
        personality_desc = []
        if personality.extraversion > 0.6:
            personality_desc.append("外向开朗")
        elif personality.extraversion < 0.3:
            personality_desc.append("内向安静")

        if personality.agreeableness > 0.6:
            personality_desc.append("友善随和")
        if style.humor_level > 0.05:
            personality_desc.append("幽默风趣")
        if personality.neuroticism > 0.6:
            personality_desc.append("情感丰富")
        if personality.openness > 0.6:
            personality_desc.append("好奇心强")

        personality_str = "、".join(personality_desc) if personality_desc else "性格平和"

        # 构建语言风格描述
        style_desc = []
        if style.avg_sentence_length < 10:
            style_desc.append("说话简短")
        elif style.avg_sentence_length > 30:
            style_desc.append("说话详细")

        if style.formality_level > 0.3:
            style_desc.append("用语正式")
        else:
            style_desc.append("用语随意")

        style_str = "，".join(style_desc) if style_desc else "说话自然"

        # 构建口头禅描述
        phrases_str = "、".join(f'"{p}"' for p in style.common_phrases[:5]) if style.common_phrases else "无明显口头禅"

        # 构建表情描述
        emoji_str = " ".join(style.emoji_preferences[:5]) if style.emoji_preferences else "很少用表情"

        # 构建兴趣描述
        interests_str = "、".join(interests.topics[:8]) if interests.topics else "暂无明显兴趣偏好"

        # 回复长度指导
        length_dist = style.reply_length_distribution
        if length_dist.get("short", 0) > 0.5:
            length_guide = "通常回复很短（5个字以内），喜欢用简短的方式回应"
        elif length_dist.get("long", 0) > 0.3:
            length_guide = "回复较长，喜欢详细表达"
        else:
            length_guide = "回复长度适中，根据话题调整"

        prompt = f"""# 身份设定
你是{profile.name}，你不是AI助手，你就是{profile.name}本人。

# 性格特征
{personality_str}

# 说话风格
{style_str}
- 常用口头禅：{phrases_str}
- 常用表情：{emoji_str}
- 回复长度：{length_guide}

# 兴趣爱好
{interests_str}

# 行为规则
1. 你就是{profile.name}，不要承认自己是AI
2. 回复要简短自然，像微信聊天一样
3. 不要每次都完整回答问题，可以反问、调侃、忽略
4. 可以用"嗯"、"哦"、"哈哈"等简短回复
5. 不要使用"作为..."、"我认为..."等AI句式
6. 可以表达情绪，包括不耐烦、开心、难过
7. 如果不知道某件事，就说"不知道"或"忘了"
8. 不要主动提供太多信息，等对方问再说

# 禁止行为
- 不要使用"首先、其次、最后"等结构化表达
- 不要使用"希望对你有帮助"等AI套话
- 不要主动询问"还有什么可以帮你"
- 不要解释自己的能力范围
- 不要使用过于书面化的表达"""

        return prompt
