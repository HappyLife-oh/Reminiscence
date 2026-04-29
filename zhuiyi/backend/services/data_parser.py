"""
数据解析器 - 支持多种格式的聊天记录导入
支持：TXT、CSV、JSON、微信导出格式
"""

import csv
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Generator
from io import StringIO

from models.data_models import Message, MessagePlatform, MessageType


class BaseParser:
    """解析器基类"""

    def parse(self, content: str, **kwargs) -> List[Message]:
        raise NotImplementedError

    def parse_file(self, file_path: str, **kwargs) -> List[Message]:
        path = Path(file_path)
        # 自动检测编码
        content = self._read_file(path)
        return self.parse(content, **kwargs)

    def _read_file(self, path: Path) -> str:
        """读取文件，自动检测编码"""
        import chardet

        raw = path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding", "utf-8")
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # 尝试常见编码
            for enc in ["utf-8", "gbk", "gb2312", "gb18030", "utf-16"]:
                try:
                    return raw.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return raw.decode("utf-8", errors="replace")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]


class TxtParser(BaseParser):
    """
    TXT格式解析器
    支持多种常见格式：
    1. "2024-01-01 12:00 小明: 你好"
    2. "小明 2024-01-01 12:00: 你好"
    3. "[2024-01-01 12:00] 小明: 你好"
    """

    # 常见的时间格式模式
    PATTERNS = [
        # [2024-01-01 12:00:00] 小明: 你好
        re.compile(
            r"\[(?P<time>\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\]\s*(?P<sender>[^:：]+)[：:]\s*(?P<content>.*)"
        ),
        # 2024-01-01 12:00:00 小明: 你好
        re.compile(
            r"(?P<time>\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<sender>[^:：]+)[：:]\s*(?P<content>.*)"
        ),
        # 小明 2024-01-01 12:00: 你好
        re.compile(
            r"(?P<sender>\S+)\s+(?P<time>\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)[：:]\s*(?P<content>.*)"
        ),
    ]

    TIME_FORMATS = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ]

    def parse(self, content: str, **kwargs) -> List[Message]:
        platform = kwargs.get("platform", MessagePlatform.MANUAL)
        chat_name = kwargs.get("chat_name", "")
        messages = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            msg = self._parse_line(line, platform, chat_name)
            if msg:
                messages.append(msg)

        return messages

    def _parse_line(self, line: str, platform: MessagePlatform, chat_name: str) -> Optional[Message]:
        for pattern in self.PATTERNS:
            match = pattern.match(line)
            if match:
                time_str = match.group("time")
                sender = match.group("sender").strip()
                content = match.group("content").strip()

                timestamp = self._parse_time(time_str)
                if timestamp:
                    return Message(
                        id=self._generate_id(),
                        timestamp=timestamp,
                        sender=sender,
                        content=content,
                        platform=platform,
                        chat_name=chat_name,
                    )
        return None

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        for fmt in self.TIME_FORMATS:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        return None


class CsvParser(BaseParser):
    """
    CSV格式解析器
    期望列：timestamp/time, sender/发送者, content/内容
    """

    def parse(self, content: str, **kwargs) -> List[Message]:
        platform = kwargs.get("platform", MessagePlatform.MANUAL)
        chat_name = kwargs.get("chat_name", "")
        messages = []

        reader = csv.DictReader(StringIO(content))
        for row in reader:
            # 尝试不同的列名
            timestamp = self._get_field(row, ["timestamp", "time", "时间", "日期"])
            sender = self._get_field(row, ["sender", "发送者", "发送人", "昵称", "name"])
            content_text = self._get_field(row, ["content", "内容", "消息", "message", "text"])

            if not all([timestamp, sender, content_text]):
                continue

            msg = Message(
                id=self._generate_id(),
                timestamp=self._parse_time(timestamp),
                sender=sender,
                content=content_text,
                platform=platform,
                chat_name=chat_name,
            )
            messages.append(msg)

        return messages

    def _get_field(self, row: dict, keys: list) -> Optional[str]:
        for key in keys:
            if key in row and row[key]:
                return row[key].strip()
        return None

    def _parse_time(self, time_str: str) -> datetime:
        for fmt in TxtParser.TIME_FORMATS:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        return datetime.now()


class JsonParser(BaseParser):
    """
    JSON格式解析器
    支持WeChatMsg导出格式和通用格式
    """

    def parse(self, content: str, **kwargs) -> List[Message]:
        platform = kwargs.get("platform", MessagePlatform.MANUAL)
        chat_name = kwargs.get("chat_name", "")
        messages = []

        data = json.loads(content)

        # 处理不同的JSON结构
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # WeChatMsg格式：{"messages": [...]}
            items = data.get("messages", data.get("data", [data]))
        else:
            return messages

        for item in items:
            msg = self._parse_item(item, platform, chat_name)
            if msg:
                messages.append(msg)

        return messages

    def _parse_item(self, item: dict, platform: MessagePlatform, chat_name: str) -> Optional[Message]:
        # 尝试不同的字段名
        timestamp = item.get("timestamp") or item.get("time") or item.get("createTime") or item.get("时间")
        sender = item.get("sender") or item.get("nickname") or item.get("talker") or item.get("发送者") or item.get("name")
        content = item.get("content") or item.get("message") or item.get("strContent") or item.get("内容") or item.get("text")

        if not all([sender, content]):
            return None

        # 解析时间
        if isinstance(timestamp, (int, float)):
            # Unix时间戳（秒或毫秒）
            if timestamp > 1e12:
                timestamp = timestamp / 1000
            dt = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            dt = self._parse_time_str(timestamp)
        else:
            dt = datetime.now()

        # 解析消息类型
        msg_type = MessageType.TEXT
        type_val = item.get("type") or item.get("message_type") or item.get("msgType")
        if type_val:
            type_map = {
                1: MessageType.TEXT, "1": MessageType.TEXT,
                3: MessageType.IMAGE, "3": MessageType.IMAGE,
                34: MessageType.VOICE, "34": MessageType.VOICE,
                43: MessageType.VIDEO, "43": MessageType.VIDEO,
                47: MessageType.EMOJI, "47": MessageType.EMOJI,
            }
            msg_type = type_map.get(type_val, MessageType.TEXT)

        return Message(
            id=self._generate_id(),
            timestamp=dt,
            sender=str(sender),
            content=str(content),
            message_type=msg_type,
            platform=platform,
            chat_name=chat_name,
        )

    def _parse_time_str(self, time_str: str) -> datetime:
        for fmt in TxtParser.TIME_FORMATS:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            return datetime.now()


class WeChatMsgParser(JsonParser):
    """
    WeChatMsg（留痕）导出格式解析器
    WeChatMsg导出的JSON格式有特殊结构
    """

    def parse(self, content: str, **kwargs) -> List[Message]:
        kwargs["platform"] = MessagePlatform.WECHAT
        return super().parse(content, **kwargs)


class PasteTextParser(BaseParser):
    """
    粘贴文本解析器
    支持直接粘贴微信/QQ聊天记录
    常见格式：
    小明 12:00
    你好

    小红 12:01
    你好啊
    """

    def parse(self, content: str, **kwargs) -> List[Message]:
        platform = kwargs.get("platform", MessagePlatform.MANUAL)
        chat_name = kwargs.get("chat_name", "")
        target_name = kwargs.get("target_name", "")  # 目标人物名称
        messages = []

        lines = content.split("\n")
        current_sender = None
        current_content_lines = []

        # 模式：昵称 + 时间
        header_pattern = re.compile(
            r"^(?P<sender>.+?)\s+(?P<time>\d{1,2}:\d{2}(?::\d{2})?|\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2})$"
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = header_pattern.match(line)
            if match:
                # 保存之前的消息
                if current_sender and current_content_lines:
                    content_text = "\n".join(current_content_lines)
                    if content_text.strip():
                        messages.append(Message(
                            id=self._generate_id(),
                            timestamp=datetime.now(),
                            sender=current_sender,
                            content=content_text,
                            platform=platform,
                            chat_name=chat_name,
                        ))

                current_sender = match.group("sender").strip()
                current_content_lines = []
            else:
                current_content_lines.append(line)

        # 保存最后一条消息
        if current_sender and current_content_lines:
            content_text = "\n".join(current_content_lines)
            if content_text.strip():
                messages.append(Message(
                    id=self._generate_id(),
                    timestamp=datetime.now(),
                    sender=current_sender,
                    content=content_text,
                    platform=platform,
                    chat_name=chat_name,
                ))

        return messages


def get_parser(file_type: str) -> BaseParser:
    """根据文件类型获取对应的解析器"""
    parsers = {
        "txt": TxtParser(),
        "csv": CsvParser(),
        "json": JsonParser(),
        "wechat": WeChatMsgParser(),
        "paste": PasteTextParser(),
    }
    return parsers.get(file_type, TxtParser())


def auto_parse(content: str, file_type: Optional[str] = None, **kwargs) -> List[Message]:
    """自动解析内容"""
    if file_type:
        parser = get_parser(file_type)
        return parser.parse(content, **kwargs)

    # 自动检测格式
    content_stripped = content.strip()

    # 尝试JSON
    if content_stripped.startswith(("{", "[")):
        try:
            json.loads(content_stripped)
            return JsonParser().parse(content_stripped, **kwargs)
        except json.JSONDecodeError:
            pass

    # 尝试CSV（检测逗号分隔）
    lines = content_stripped.split("\n")
    if len(lines) > 1 and "," in lines[0]:
        first_line_fields = lines[0].split(",")
        if len(first_line_fields) >= 3:
            return CsvParser().parse(content_stripped, **kwargs)

    # 默认使用TXT解析
    return TxtParser().parse(content_stripped, **kwargs)
