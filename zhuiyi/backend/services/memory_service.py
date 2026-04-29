"""
记忆管理服务 - 三层记忆架构
短期记忆：当前对话上下文
工作记忆：RAG检索相关记忆
长期记忆：系统提示词中的人格特征
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import chromadb
from chromadb.config import Settings

from models.data_models import Message


# ChromaDB存储目录
MEMORY_DIR = Path.home() / ".zhuiyi" / "memory"


class MemoryService:
    """记忆管理服务"""

    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory=str(MEMORY_DIR),
        ))
        self._collections: Dict[str, chromadb.Collection] = {}

    def _get_collection(self, character_id: str) -> chromadb.Collection:
        """获取或创建人物的记忆集合"""
        if character_id not in self._collections:
            collection_name = f"memory_{character_id.replace('-', '_')}"
            self._collections[character_id] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[character_id]

    def add_messages(self, character_id: str, messages: List[Message]) -> int:
        """将消息添加到记忆中"""
        collection = self._get_collection(character_id)

        documents = []
        ids = []
        metadatas = []

        for msg in messages:
            if not msg.content or len(msg.content.strip()) < 2:
                continue

            # 跳过系统消息
            if msg.sender in ["system", "System"]:
                continue

            doc_id = f"{character_id}_{msg.id}"
            documents.append(msg.content)
            ids.append(doc_id)
            metadatas.append({
                "sender": msg.sender,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else "",
                "platform": msg.platform.value if msg.platform else "manual",
                "chat_name": msg.chat_name or "",
                "message_type": msg.message_type.value if msg.message_type else "text",
            })

        if documents:
            # 分批添加（ChromaDB有批量限制）
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]

                try:
                    collection.upsert(
                        documents=batch_docs,
                        ids=batch_ids,
                        metadatas=batch_metas,
                    )
                except Exception as e:
                    print(f"[WARN] 添加记忆失败: {e}")

        return len(documents)

    def search_memories(
        self,
        character_id: str,
        query: str,
        top_k: int = 5,
        sender_filter: Optional[str] = None,
    ) -> List[Dict]:
        """搜索相关记忆"""
        collection = self._get_collection(character_id)

        # 检查集合是否有数据
        if collection.count() == 0:
            return []

        where_filter = None
        if sender_filter:
            where_filter = {"sender": sender_filter}

        try:
            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count()),
                where=where_filter,
            )
        except Exception as e:
            print(f"[WARN] 搜索记忆失败: {e}")
            return []

        memories = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                memory = {
                    "content": doc,
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                }
                memories.append(memory)

        return memories

    def get_context_memories(
        self,
        character_id: str,
        current_message: str,
        recent_messages: List[Message],
        top_k: int = 3,
    ) -> str:
        """获取上下文记忆，用于注入Prompt"""
        # 搜索语义相关的记忆
        memories = self.search_memories(
            character_id=character_id,
            query=current_message,
            top_k=top_k,
        )

        if not memories:
            return ""

        # 构建记忆文本
        memory_texts = []
        for mem in memories:
            sender = mem["metadata"].get("sender", "未知")
            content = mem["content"]
            # 截断过长的内容
            if len(content) > 100:
                content = content[:100] + "..."
            memory_texts.append(f"{sender}: {content}")

        return "\n".join(memory_texts)

    def get_memory_stats(self, character_id: str) -> Dict:
        """获取记忆统计信息"""
        collection = self._get_collection(character_id)
        count = collection.count()

        return {
            "character_id": character_id,
            "total_memories": count,
        }

    def delete_memories(self, character_id: str) -> bool:
        """删除人物的所有记忆"""
        try:
            collection_name = f"memory_{character_id.replace('-', '_')}"
            self.client.delete_collection(collection_name)
            if character_id in self._collections:
                del self._collections[character_id]
            return True
        except Exception:
            return False
