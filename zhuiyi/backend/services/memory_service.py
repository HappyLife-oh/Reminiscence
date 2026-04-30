"""
记忆管理服务 - 三层记忆架构
短期记忆：当前对话上下文
工作记忆：RAG检索相关记忆
长期记忆：系统提示词中的人格特征

使用轻量级内存向量存储，避免ChromaDB的sqlite3版本问题
"""

import json
import uuid
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from models.data_models import Message


# 记忆存储目录
MEMORY_DIR = Path.home() / ".zhuiyi" / "memory"


class SimpleVectorStore:
    """轻量级向量存储，基于numpy实现"""

    def __init__(self):
        self.documents: List[str] = []
        self.ids: List[str] = []
        self.metadatas: List[Dict] = []
        self.vectors: List[List[float]] = []
        self._embedding_model = None

    def _get_embedding_model(self):
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception:
                self._embedding_model = None
        return self._embedding_model

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """文本向量化"""
        model = self._get_embedding_model()
        if model:
            embeddings = model.encode(texts)
            return embeddings.tolist()
        else:
            # 降级：使用简单的字符级哈希作为向量
            return [self._simple_hash_vector(t) for t in texts]

    def _simple_hash_vector(self, text: str, dim: int = 384) -> List[float]:
        """简单的字符级哈希向量（降级方案）"""
        import hashlib
        vec = [0.0] * dim
        for i, char in enumerate(text):
            h = int(hashlib.md5(char.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
        # 归一化
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def add(self, documents: List[str], ids: List[str], metadatas: List[Dict]):
        """添加文档"""
        vectors = self._embed(documents)
        for doc, id_, meta, vec in zip(documents, ids, metadatas, vectors):
            # 更新已存在的文档
            if id_ in self.ids:
                idx = self.ids.index(id_)
                self.documents[idx] = doc
                self.metadatas[idx] = meta
                self.vectors[idx] = vec
            else:
                self.documents.append(doc)
                self.ids.append(id_)
                self.metadatas.append(meta)
                self.vectors.append(vec)

    def query(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """查询相似文档"""
        if not self.documents:
            return []

        query_vec = self._embed([query_text])[0]

        # 计算余弦相似度
        similarities = []
        for vec in self.vectors:
            sim = self._cosine_similarity(query_vec, vec)
            similarities.append(sim)

        # 排序取top-k
        indexed_sims = [(i, sim) for i, sim in enumerate(similarities)]
        indexed_sims.sort(key=lambda x: x[1], reverse=True)

        results = []
        for i, sim in indexed_sims[:n_results]:
            results.append({
                "content": self.documents[i],
                "distance": 1 - sim,  # 转换为距离
                "metadata": self.metadatas[i],
            })

        return results

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def count(self) -> int:
        return len(self.documents)

    def save(self, path: str):
        """保存到文件"""
        data = {
            "documents": self.documents,
            "ids": self.ids,
            "metadatas": self.metadatas,
            "vectors": self.vectors,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path: str):
        """从文件加载"""
        if not Path(path).exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.documents = data.get("documents", [])
        self.ids = data.get("ids", [])
        self.metadatas = data.get("metadatas", [])
        self.vectors = data.get("vectors", [])


class MemoryService:
    """记忆管理服务"""

    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._stores: Dict[str, SimpleVectorStore] = {}

    def _get_store(self, character_id: str) -> SimpleVectorStore:
        """获取或创建人物的记忆存储"""
        if character_id not in self._stores:
            store = SimpleVectorStore()
            # 尝试从文件加载
            store_path = MEMORY_DIR / f"{character_id}.json"
            if store_path.exists():
                store.load(str(store_path))
            self._stores[character_id] = store
        return self._stores[character_id]

    def _save_store(self, character_id: str):
        """保存记忆到文件"""
        if character_id in self._stores:
            store_path = MEMORY_DIR / f"{character_id}.json"
            self._stores[character_id].save(str(store_path))

    def add_messages(self, character_id: str, messages: List[Message]) -> int:
        """将消息添加到记忆中"""
        store = self._get_store(character_id)

        documents = []
        ids = []
        metadatas = []

        for msg in messages:
            if not msg.content or len(msg.content.strip()) < 2:
                continue
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
            })

        if documents:
            store.add(documents, ids, metadatas)
            self._save_store(character_id)

        return len(documents)

    def search_memories(
        self,
        character_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """搜索相关记忆"""
        store = self._get_store(character_id)
        if store.count() == 0:
            return []
        return store.query(query, min(top_k, store.count()))

    def get_context_memories(
        self,
        character_id: str,
        current_message: str,
        recent_messages: List[Message],
        top_k: int = 3,
    ) -> str:
        """获取上下文记忆，用于注入Prompt"""
        memories = self.search_memories(
            character_id=character_id,
            query=current_message,
            top_k=top_k,
        )

        if not memories:
            return ""

        memory_texts = []
        for mem in memories:
            sender = mem["metadata"].get("sender", "未知")
            content = mem["content"]
            if len(content) > 100:
                content = content[:100] + "..."
            memory_texts.append(f"{sender}: {content}")

        return "\n".join(memory_texts)

    def get_memory_stats(self, character_id: str) -> Dict:
        """获取记忆统计信息"""
        store = self._get_store(character_id)
        return {
            "character_id": character_id,
            "total_memories": store.count(),
        }

    def delete_memories(self, character_id: str) -> bool:
        """删除人物的所有记忆"""
        try:
            if character_id in self._stores:
                del self._stores[character_id]
            store_path = MEMORY_DIR / f"{character_id}.json"
            if store_path.exists():
                store_path.unlink()
            return True
        except Exception:
            return False
