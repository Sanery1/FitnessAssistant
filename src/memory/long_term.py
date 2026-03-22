"""
Long-term memory (Persistent storage)

管理用户数据的持久化存储，包括用户档案、训练记录、身体数据等。
"""
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from pathlib import Path
from .base import BaseMemory, MemoryItem


class LongTermMemory(BaseMemory):
    """长期记忆 - 持久化存储"""

    def __init__(self, storage_path: str = "data/memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, MemoryItem] = {}
        self._user_data: Dict[str, Any] = {}

    def _get_file_path(self, key: str) -> Path:
        """获取存储文件路径"""
        # 处理特殊字符
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_key}.json"

    def _load_from_file(self, key: str) -> Optional[MemoryItem]:
        """从文件加载"""
        file_path = self._get_file_path(key)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return MemoryItem(**data)
            except Exception:
                pass
        return None

    def _save_to_file(self, key: str, item: MemoryItem) -> None:
        """保存到文件"""
        file_path = self._get_file_path(key)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(item.model_dump(), f, ensure_ascii=False, default=str)

    # BaseMemory 接口实现
    def add(self, item: MemoryItem) -> None:
        """添加记忆项"""
        key = item.metadata.get("key", f"item_{datetime.now().timestamp()}")
        self._cache[key] = item
        self._save_to_file(key, item)

    def get(self, key: str) -> Optional[MemoryItem]:
        """获取记忆"""
        # 先查缓存
        if key in self._cache:
            return self._cache[key]
        # 再查文件
        item = self._load_from_file(key)
        if item:
            self._cache[key] = item
        return item

    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        items = []
        for file_path in self.storage_path.glob("*.json"):
            key = file_path.stem
            item = self.get(key)
            if item:
                items.append(item)
        return items

    def clear(self) -> None:
        """清空记忆 (危险操作)"""
        self._cache.clear()
        for file_path in self.storage_path.glob("*.json"):
            file_path.unlink()

    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索记忆 (简单实现)"""
        results = []
        query_lower = query.lower()

        for item in self.get_all():
            content_str = str(item.content).lower()
            if query_lower in content_str:
                results.append(item)
                if len(results) >= limit:
                    break

        return results

    # 用户数据管理
    def save_user_profile(self, user_id: str, profile: Dict) -> None:
        """保存用户档案"""
        key = f"user_profile_{user_id}"
        self.add(MemoryItem(
            content=profile,
            metadata={"key": key, "type": "user_profile", "user_id": user_id},
            importance=1.0
        ))

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户档案"""
        key = f"user_profile_{user_id}"
        item = self.get(key)
        return item.content if item else None

    def save_workout_history(self, user_id: str, workout: Dict) -> None:
        """保存训练记录"""
        key = f"workout_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.add(MemoryItem(
            content=workout,
            metadata={"key": key, "type": "workout", "user_id": user_id},
            importance=0.7
        ))

    def get_workout_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取训练历史"""
        workouts = []
        for item in self.get_all():
            if (item.metadata.get("type") == "workout" and
                item.metadata.get("user_id") == user_id):
                workouts.append(item.content)

        # 按日期排序
        workouts.sort(key=lambda x: x.get("date", ""), reverse=True)
        return workouts[:limit]

    def save_body_data(self, user_id: str, data: Dict) -> None:
        """保存身体数据"""
        key = f"body_{user_id}_{data.get('date', datetime.now().strftime('%Y%m%d'))}"
        self.add(MemoryItem(
            content=data,
            metadata={"key": key, "type": "body_data", "user_id": user_id},
            importance=0.8
        ))

    def get_body_data_history(self, user_id: str, limit: int = 30) -> List[Dict]:
        """获取身体数据历史"""
        records = []
        for item in self.get_all():
            if (item.metadata.get("type") == "body_data" and
                item.metadata.get("user_id") == user_id):
                records.append(item.content)

        records.sort(key=lambda x: x.get("date", ""), reverse=True)
        return records[:limit]

    # 统计
    def get_stats(self) -> Dict:
        """获取存储统计"""
        items = self.get_all()
        return {
            "total_items": len(items),
            "by_type": self._count_by_type(items),
            "storage_path": str(self.storage_path)
        }

    def _count_by_type(self, items: List[MemoryItem]) -> Dict[str, int]:
        """按类型统计"""
        counts = {}
        for item in items:
            type_name = item.metadata.get("type", "unknown")
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
