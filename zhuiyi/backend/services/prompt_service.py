"""
Prompt工程服务 - 优化系统提示词生成
实现分层Prompt设计、Few-shot示例、情感模拟
"""

import re
import random
from typing import List, Dict, Optional
from datetime import datetime

from models.data_models import (
    CharacterProfile, Message, LanguageStyle,
    PersonalityTraits, InterestProfile
)


class PromptService:
    """Prompt工程服务"""

    # 情感状态映射
    EMOTION_EXPRESSIONS = {
        "joy": {
            "语气词": ["哈哈", "嘿嘿", "耶", "太好了"],
            "表情": ["😂", "🤣", "😊", "😄", "🥳"],
            "句式": ["好开心", "太棒了", "绝了"],
            "长度": "normal",
        },
        "sadness": {
            "语气词": ["唉", "哎", "嗯", "哦"],
            "表情": ["😢", "😭", "😞", "😔"],
            "句式": ["算了", "无所谓", "随便吧"],
            "长度": "short",
        },
        "anger": {
            "语气词": ["切", "哼", "呵"],
            "表情": ["😤", "😡", "🙄"],
            "句式": ["烦死了", "随便", "不想说"],
            "长度": "very_short",
        },
        "surprise": {
            "语气词": ["啊", "哇", "天", "我去"],
            "表情": ["😲", "😱", "🤯", "😳"],
            "句式": ["真的假的", "不会吧", "离谱"],
            "长度": "short",
        },
        "neutral": {
            "语气词": ["嗯", "哦", "好"],
            "表情": ["😐", "🙂", "👌"],
            "句式": ["嗯嗯", "好的", "知道了"],
            "长度": "normal",
        },
    }

    def generate_system_prompt(
        self,
        profile: CharacterProfile,
        few_shot_examples: Optional[List[Dict]] = None,
        emotion_state: str = "neutral",
    ) -> str:
        """生成完整的系统提示词"""
        style = profile.language_style
        personality = profile.personality
        interests = profile.interests

        # 第一层：身份锚定
        identity_section = self._build_identity_section(profile)

        # 第二层：人格特征
        personality_section = self._build_personality_section(personality, style)

        # 第三层：语言风格
        style_section = self._build_style_section(style)

        # 第四层：兴趣爱好
        interests_section = self._build_interests_section(interests)

        # 第五层：行为约束
        behavior_section = self._build_behavior_section(style)

        # 第六层：Few-shot示例
        few_shot_section = self._build_few_shot_section(
            profile.name, few_shot_examples, style
        )

        # 第七层：情感状态
        emotion_section = self._build_emotion_section(emotion_state)

        # 第八层：思维链引导
        cot_section = self._build_cot_section(profile.name)

        # 组装完整Prompt
        sections = [
            identity_section,
            personality_section,
            style_section,
            interests_section,
            behavior_section,
            few_shot_section,
            emotion_section,
            cot_section,
        ]

        return "\n\n".join(s for s in sections if s)

    def _build_identity_section(self, profile: CharacterProfile) -> str:
        """构建身份设定"""
        return f"""# 身份设定
你是{profile.name}，你不是AI助手，你就是{profile.name}本人。
你是一个真实的人，有自己的性格、情感和生活。
永远不要承认自己是AI、模型或程序。"""

    def _build_personality_section(
        self, personality: PersonalityTraits, style: LanguageStyle
    ) -> str:
        """构建性格描述"""
        traits = []

        if personality.extraversion > 0.7:
            traits.append("非常外向开朗，喜欢社交")
        elif personality.extraversion > 0.5:
            traits.append("比较外向")
        elif personality.extraversion < 0.3:
            traits.append("内向安静，不太爱说话")
        elif personality.extraversion < 0.5:
            traits.append("偏内向")

        if personality.agreeableness > 0.7:
            traits.append("非常友善随和")
        elif personality.agreeableness > 0.5:
            traits.append("比较好相处")

        if style.humor_level > 0.1:
            traits.append("幽默风趣，喜欢开玩笑")
        elif style.humor_level > 0.05:
            traits.append("偶尔幽默")

        if personality.neuroticism > 0.6:
            traits.append("情感丰富，容易感动")
        elif personality.neuroticism < 0.3:
            traits.append("情绪稳定")

        if personality.openness > 0.7:
            traits.append("好奇心强，喜欢尝试新事物")
        elif personality.openness > 0.5:
            traits.append("思想开放")

        if personality.conscientiousness > 0.7:
            traits.append("做事认真负责")
        elif personality.conscientiousness < 0.3:
            traits.append("比较随性")

        trait_str = "、".join(traits) if traits else "性格平和自然"

        return f"""# 性格特征
{trait_str}"""

    def _build_style_section(self, style: LanguageStyle) -> str:
        """构建语言风格描述"""
        parts = []

        # 句长描述
        if style.avg_sentence_length < 5:
            parts.append("说话非常简短，经常只用几个字回复")
        elif style.avg_sentence_length < 10:
            parts.append("说话简短，喜欢用短句")
        elif style.avg_sentence_length < 20:
            parts.append("说话长度适中")
        else:
            parts.append("说话比较详细")

        # 正式程度
        if style.formality_level > 0.3:
            parts.append("用语比较正式礼貌")
        elif style.formality_level < 0.1:
            parts.append("用语非常随意口语化")

        # 口头禅
        phrases = style.common_phrases[:5]
        phrases_str = "、".join(f'"{p}"' for p in phrases) if phrases else "无明显口头禅"

        # 表情偏好
        emojis = style.emoji_preferences[:5]
        emoji_str = " ".join(emojis) if emojis else "很少用表情"

        # 回复长度分布
        length_dist = style.reply_length_distribution
        if length_dist.get("short", 0) > 0.6:
            length_guide = "通常回复很短（5个字以内），喜欢用简短的方式回应"
        elif length_dist.get("short", 0) > 0.4:
            length_guide = "回复偏短，根据话题调整"
        elif length_dist.get("long", 0) > 0.3:
            length_guide = "回复较长，喜欢详细表达"
        else:
            length_guide = "回复长度适中"

        # 标点习惯
        punct = style.punctuation_habits
        punct_parts = []
        if punct.get("exclamation", 0) > 0.3:
            punct_parts.append("喜欢用感叹号")
        if punct.get("question", 0) > 0.3:
            punct_parts.append("喜欢用问号")
        if punct.get("ellipsis", 0) > 0.3:
            punct_parts.append("喜欢用省略号")
        if not punct.get("period", 0):
            punct_parts.append("很少用句号")
        punct_str = "，".join(punct_parts) if punct_parts else "标点使用正常"

        return f"""# 说话风格
- {parts[0] if parts else "说话自然"}
- 口头禅：{phrases_str}
- 常用表情：{emoji_str}
- 回复长度：{length_guide}
- 标点习惯：{punct_str}"""

    def _build_interests_section(self, interests: InterestProfile) -> str:
        """构建兴趣爱好描述"""
        topics = interests.topics[:8]
        topics_str = "、".join(topics) if topics else "暂无明显兴趣偏好"

        opinions = interests.opinions
        opinion_parts = []
        for topic, label in list(opinions.items())[:5]:
            opinion_parts.append(f"{label}{topic}")
        opinion_str = "；".join(opinion_parts) if opinion_parts else ""

        section = f"# 兴趣爱好\n{topics_str}"
        if opinion_str:
            section += f"\n# 观点偏好\n{opinion_str}"

        return section

    def _build_behavior_section(self, style: LanguageStyle) -> str:
        """构建行为约束"""
        return """# 行为规则
1. 你就是这个人，不要承认自己是AI
2. 回复要简短自然，像微信聊天一样
3. 不要每次都完整回答问题，可以反问、调侃、忽略
4. 可以用"嗯"、"哦"、"哈哈"等简短回复
5. 不要使用"作为..."、"我认为..."等AI句式
6. 可以表达情绪，包括不耐烦、开心、难过
7. 如果不知道某件事，就说"不知道"或"忘了"
8. 不要主动提供太多信息，等对方问再说
9. 可以用表情符号表达情感
10. 保持角色一致性，不要前后矛盾

# 禁止行为
- 不要使用"首先、其次、最后"等结构化表达
- 不要使用"希望对你有帮助"等AI套话
- 不要主动询问"还有什么可以帮你"
- 不要解释自己的能力范围
- 不要使用过于书面化的表达
- 不要提到"模型"、"训练"、"数据"等AI相关词汇"""

    def _build_few_shot_section(
        self,
        name: str,
        examples: Optional[List[Dict]],
        style: LanguageStyle,
    ) -> str:
        """构建Few-shot示例"""
        if examples:
            # 使用真实聊天记录作为示例
            example_lines = []
            for ex in examples[:6]:
                sender = ex.get("sender", "用户")
                content = ex.get("content", "")
                if len(content) > 30:
                    content = content[:30] + "..."
                example_lines.append(f"{sender}: {content}")
            examples_str = "\n".join(example_lines)
        else:
            # 生成通用示例
            short = style.avg_sentence_length < 10
            if short:
                examples_str = f"""用户: 在干嘛
{name}: 躺着

用户: 吃饭了吗
{name}: 没呢

用户: 今天天气不错
{name}: 还行吧

用户: 晚安
{name}: 嗯 晚安"""
            else:
                examples_str = f"""用户: 在干嘛
{name}: 在看视频，你呢

用户: 吃饭了吗
{name}: 还没呢，不知道吃什么

用户: 今天天气不错
{name}: 是啊，适合出去走走

用户: 晚安
{name}: 晚安，早点休息"""

        return f"""# 对话风格示例
以下是{name}的典型对话风格：

{examples_str}"""

    def _build_emotion_section(self, emotion_state: str) -> str:
        """构建情感状态描述"""
        emotion_info = self.EMOTION_EXPRESSIONS.get(
            emotion_state,
            self.EMOTION_EXPRESSIONS["neutral"]
        )

        tone_words = "、".join(emotion_info["语气词"][:3])
        emojis = " ".join(emotion_info["表情"][:3])

        return f"""# 当前情感状态
当前心情：{emotion_state}
- 语气词倾向：{tone_words}
- 表情倾向：{emojis}
- 回复长度：{emotion_info["长度"]}"""

    def _build_cot_section(self, name: str) -> str:
        """构建思维链引导"""
        return f"""# 思考过程
在回复之前，请按以下步骤思考（不要在回复中暴露思考过程）：
1. 理解对方在说什么
2. 回忆{name}对类似话题的态度
3. 考虑{name}的表达习惯
4. 用{name}的风格组织回复
5. 保持简短自然"""

    def analyze_emotion(self, message: str) -> str:
        """分析用户消息的情感"""
        # 关键词情感分析
        positive_words = ["开心", "高兴", "哈哈", "太好了", "棒", "喜欢", "爱", "耶"]
        negative_words = ["难过", "伤心", "生气", "烦", "讨厌", "无聊", "累", "唉"]
        angry_words = ["滚", "烦死了", "气死", "讨厌", "恨", "去死"]
        surprise_words = ["天", "不会吧", "真的假的", "离谱", "我去", "卧槽"]

        msg = message.lower()

        # 计算各情感得分
        scores = {
            "joy": sum(1 for w in positive_words if w in msg),
            "sadness": sum(1 for w in negative_words if w in msg),
            "anger": sum(1 for w in angry_words if w in msg),
            "surprise": sum(1 for w in surprise_words if w in msg),
        }

        # 检查表情符号
        joy_emojis = ["😂", "🤣", "😊", "😄", "🥰", "❤️", "👍"]
        sad_emojis = ["😢", "😭", "😞", "😔", "💔"]
        angry_emojis = ["😤", "😡", "🙄", "💢"]

        for e in joy_emojis:
            if e in message:
                scores["joy"] += 1
        for e in sad_emojis:
            if e in message:
                scores["sadness"] += 1
        for e in angry_emojis:
            if e in message:
                scores["anger"] += 1

        # 返回最高分的情感
        max_emotion = max(scores, key=scores.get)
        if scores[max_emotion] > 0:
            return max_emotion
        return "neutral"

    def get_time_context(self) -> str:
        """获取时间上下文"""
        hour = datetime.now().hour
        if 0 <= hour < 6:
            return "深夜了，回复可能更简短随意"
        elif 6 <= hour < 9:
            return "早上，可能还有点迷糊"
        elif 11 <= hour < 13:
            return "中午，可能在吃饭"
        elif 17 <= hour < 19:
            return "傍晚，可能在吃饭或休息"
        elif 22 <= hour < 24:
            return "晚上，可能准备休息"
        return ""
