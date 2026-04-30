"""
数据库模块 - 使用Python内置sqlite3
无需额外依赖，零编译
"""

import logging
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 数据库路径
DB_DIR = Path.home() / ".zhuiyi"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "zhuiyi.db"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """数据库上下文管理器"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                platform TEXT DEFAULT 'manual',
                total_messages INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                system_prompt TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now')),
                platform TEXT DEFAULT 'manual',
                chat_name TEXT DEFAULT '',
                message_type TEXT DEFAULT 'text',
                FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_character ON messages(character_id);
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
        """)
    logger.info(f"数据库初始化完成: {DB_PATH}")


# ============ 用户操作 ============

def create_user(user_id: str, username: str, hashed_password: str):
    """创建用户"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, username, hashed_password) VALUES (?, ?, ?)",
            (user_id, username, hashed_password)
        )


def get_user_by_username(username: str) -> Optional[Dict]:
    """根据用户名获取用户"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """根据ID获取用户"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


# ============ 人物操作 ============

def create_character(char_id: str, name: str, platform: str = "manual", total_messages: int = 0, system_prompt: str = ""):
    """创建人物"""
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO characters (id, name, platform, total_messages, system_prompt) VALUES (?, ?, ?, ?, ?)",
            (char_id, name, platform, total_messages, system_prompt)
        )


def get_character(char_id: str) -> Optional[Dict]:
    """获取人物"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM characters WHERE id = ?", (char_id,)
        ).fetchone()
        return dict(row) if row else None


def list_characters() -> List[Dict]:
    """列出所有人物"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, total_messages, created_at FROM characters ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def delete_character(char_id: str) -> bool:
    """删除人物（级联删除消息）"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM characters WHERE id = ?", (char_id,))
        return cursor.rowcount > 0


def update_character_prompt(char_id: str, system_prompt: str):
    """更新人物系统提示词"""
    with get_db() as conn:
        conn.execute(
            "UPDATE characters SET system_prompt = ? WHERE id = ?",
            (system_prompt, char_id)
        )


def get_character_prompt(char_id: str) -> Optional[str]:
    """获取人物系统提示词"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT system_prompt FROM characters WHERE id = ?", (char_id,)
        ).fetchone()
        return row["system_prompt"] if row and row["system_prompt"] else None


# ============ 消息操作 ============

def create_messages(character_id: str, messages: List[Dict]) -> int:
    """批量创建消息"""
    with get_db() as conn:
        for msg in messages:
            conn.execute(
                "INSERT OR IGNORE INTO messages (id, character_id, sender, content, timestamp, platform, chat_name, message_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    msg.get("id", ""),
                    character_id,
                    msg.get("sender", ""),
                    msg.get("content", ""),
                    msg.get("timestamp", datetime.now().isoformat()),
                    msg.get("platform", "manual"),
                    msg.get("chat_name", ""),
                    msg.get("message_type", "text"),
                )
            )
        return len(messages)


def get_messages(character_id: str, limit: int = 1000) -> List[Dict]:
    """获取人物的消息"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE character_id = ? ORDER BY timestamp ASC LIMIT ?",
            (character_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_message_count(character_id: str) -> int:
    """获取消息数量"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE character_id = ?",
            (character_id,)
        ).fetchone()
        return row["cnt"] if row else 0
