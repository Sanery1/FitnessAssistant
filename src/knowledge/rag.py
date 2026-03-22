"""
RAG Knowledge Base

向量检索增强生成，为 AI 提供专业知识支持。
"""
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np


class SimpleEmbedding:
    """简单的文本嵌入 (基于关键词的向量表示)

    生产环境应使用:
    - OpenAI embeddings
    - 本地模型如 sentence-transformers
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        # 简单的特征词映射
        self.feature_words = [
            "训练", "健身", "力量", "有氧", "肌肉", "胸部", "背部", "腿部", "肩部", "手臂",
            "深蹲", "卧推", "硬拉", "引体", "俯卧撑", "划船", "推举",
            "营养", "蛋白质", "碳水", "脂肪", "热量", "饮食", "减脂", "增肌",
            "恢复", "休息", "睡眠", "拉伸", "热身", "放松",
            "强度", "次数", "组数", "重量", "频率", "周期",
            "初学者", "中级", "高级", "专家",
            "核心", "全身"
        ]
        self.word_to_idx = {w: i for i, w in enumerate(self.feature_words)}

    def encode(self, text: str) -> np.ndarray:
        """编码文本为向量"""
        vector = np.zeros(self.dim)
        words = text.lower()

        for word, idx in self.word_to_idx.items():
            if word in words:
                count = words.count(word)
                vector[idx] = count

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.astype(np.float32)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """批量编码"""
        return np.array([self.encode(t) for t in texts])


class KnowledgeDocument:
    """知识文档"""

    def __init__(
        self,
        id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        embedding: np.ndarray = None
    ):
        self.id = id
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding


class VectorStore:
    """向量存储 (基于 NumPy 的简单实现)"""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.documents: List[KnowledgeDocument] = []
        self.embeddings: np.ndarray = None

    def add(self, docs: List[KnowledgeDocument]) -> None:
        """添加文档"""
        self.documents.extend(docs)

        embeddings = [d.embedding for d in docs if d.embedding is not None]
        if embeddings:
            if self.embeddings is None:
                self.embeddings = np.array(embeddings)
            else:
                self.embeddings = np.vstack([self.embeddings, np.array(embeddings)])

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[KnowledgeDocument, float]]:
        """搜索最相似的文档"""
        if self.embeddings is None or len(self.documents) == 0:
            return []

        similarities = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            score = float(similarities[idx])
            results.append((doc, score))

        return results

    def clear(self) -> None:
        """清空"""
        self.documents = []
        self.embeddings = None

    def save(self, path: str) -> None:
        """保存到文件"""
        data = {
            "documents": [
                {"id": d.id, "content": d.content, "metadata": d.metadata}
                for d in self.documents
            ],
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else None
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path: str) -> None:
        """从文件加载"""
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.documents = [
            KnowledgeDocument(id=d["id"], content=d["content"], metadata=d.get("metadata", {}))
            for d in data.get("documents", [])
        ]

        if data.get("embeddings") is not None:
            self.embeddings = np.array(data["embeddings"])


class KnowledgeBase:
    """知识库"""

    def __init__(self, data_path: str = "data/knowledge"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)

        self.embedding_model = SimpleEmbedding()
        self.vector_store = VectorStore()

        # 尝试加载已有数据
        index_path = self.data_path / "index.json"
        if index_path.exists():
            self.vector_store.load(str(index_path))

    def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """添加文档"""
        # 计算嵌入
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = self.embedding_model.encode(doc.content)

        self.vector_store.add(documents)
        self._save()

    def search(self, query: str, k: int = 5) -> List[Tuple[KnowledgeDocument, float]]:
        """检索相关文档"""
        query_embedding = self.embedding_model.encode(query)
        return self.vector_store.search(query_embedding, k)

    def get_context(self, query: str, k: int = 3) -> str:
        """获取检索上下文"""
        results = self.search(query, k)
        if not results:
            return ""

        context_parts = []
        for doc, score in results:
            context_parts.append(f"[相关度: {score:.2f}] {doc.content}")

        return "\n\n".join(context_parts)

    def _save(self) -> None:
        """保存索引"""
        index_path = self.data_path / "index.json"
        self.vector_store.save(str(index_path))


def init_fitness_knowledge(kb: KnowledgeBase) -> None:
    """初始化健身知识库"""
    if len(kb.vector_store.documents) > 0:
        return  # 已有数据，跳过

    documents = [
        # 训练知识
        KnowledgeDocument(
            id="workout_001",
            content="深蹲是训练腿部和核心力量的最佳动作。正确姿势：双脚与肩同宽，下蹲时膝盖不超过脚尖，背部保持挺直。建议每周训练2-3次，每次3-4组，每组8-12次。",
            metadata={"category": "训练", "target": "腿部", "level": "初学者"}
        ),
        KnowledgeDocument(
            id="workout_002",
            content="卧推主要锻炼胸肌、三角肌前束和肱三头肌。动作要点：肩胛骨收紧贴紧凳面，下放时肘部呈45度角，推起时呼气。初学者建议空杆开始，逐步增加重量。",
            metadata={"category": "训练", "target": "胸部", "level": "初学者"}
        ),
        KnowledgeDocument(
            id="workout_003",
            content="硬拉是全身性复合动作，主要锻炼背部、臀部和腿部。技术要点：保持脊柱中立，用髋关节铰链运动，杠铃贴近身体。初学者建议从轻重量开始学习正确姿势。",
            metadata={"category": "训练", "target": "背部", "level": "中级"}
        ),
        KnowledgeDocument(
            id="workout_004",
            content="引体向上是徒手训练背部的黄金动作。标准动作：双手略宽于肩，完全下放后拉起至下巴过杠。无法完成者可使用弹力带辅助或做跳跃式引体。",
            metadata={"category": "训练", "target": "背部", "level": "中级"}
        ),
        KnowledgeDocument(
            id="workout_005",
            content="俯卧撑是最基础的推类动作，锻炼胸肌、肩部和手臂。标准姿势：身体呈直线，核心收紧，下放至胸部接近地面。可做跪姿俯卧撑作为退阶训练。",
            metadata={"category": "训练", "target": "胸部", "level": "初学者"}
        ),
        # 营养知识
        KnowledgeDocument(
            id="nutrition_001",
            content="蛋白质是肌肉生长的关键营养素。健身人群建议每日摄入1.6-2.2克/公斤体重。优质蛋白来源：鸡胸肉、鸡蛋、鱼类、牛肉、豆腐、乳制品。",
            metadata={"category": "营养", "topic": "蛋白质"}
        ),
        KnowledgeDocument(
            id="nutrition_002",
            content="碳水化合物是训练的主要能量来源。训练前2-3小时应摄入复合碳水，如燕麦、全麦面包；训练后可补充简单碳水帮助恢复。",
            metadata={"category": "营养", "topic": "碳水"}
        ),
        KnowledgeDocument(
            id="nutrition_003",
            content="减脂的核心是热量缺口，建议每日减少300-500大卡。同时保持高蛋白饮食（防止肌肉流失）和力量训练。避免过度节食导致代谢下降。",
            metadata={"category": "营养", "topic": "减脂"}
        ),
        KnowledgeDocument(
            id="nutrition_004",
            content="增肌需要热量盈余，建议每日多摄入200-300大卡。重点：训练后30分钟内补充蛋白质和碳水，促进肌肉合成和恢复。",
            metadata={"category": "营养", "topic": "增肌"}
        ),
        # 恢复知识
        KnowledgeDocument(
            id="recovery_001",
            content="睡眠是肌肉恢复的关键时期。建议每晚7-9小时睡眠。睡眠不足会影响生长激素分泌，降低训练效果和恢复能力。",
            metadata={"category": "恢复", "topic": "睡眠"}
        ),
        KnowledgeDocument(
            id="recovery_002",
            content="训练后拉伸有助于减少肌肉紧张，提高柔韧性。每个肌群静态拉伸15-30秒，避免在训练前做长时间静态拉伸（可能影响力量表现）。",
            metadata={"category": "恢复", "topic": "拉伸"}
        ),
        KnowledgeDocument(
            id="recovery_003",
            content="休息日同样重要。肌肉在休息时生长，而非训练时。建议每周安排1-2个完全休息日，或进行低强度活动如散步、瑜伽。",
            metadata={"category": "恢复", "topic": "休息"}
        ),
        # 训练原则
        KnowledgeDocument(
            id="principle_001",
            content="渐进超负荷是肌肉增长的核心原则。可通过增加重量、增加次数、增加组数、缩短休息时间等方式实现渐进。记录训练数据很重要。",
            metadata={"category": "原则", "topic": "渐进超负荷"}
        ),
        KnowledgeDocument(
            id="principle_002",
            content="训练频率：每个肌群建议每周训练2-3次。新手可采用全身训练，中高阶者可采用分化训练。重要的是保持一致性和渐进性。",
            metadata={"category": "原则", "topic": "频率"}
        ),
    ]

    kb.add_documents(documents)
    print(f"[OK] Loaded {len(documents)} fitness knowledge documents")