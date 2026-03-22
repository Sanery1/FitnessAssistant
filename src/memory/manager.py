"""
Memory Manager

统一管理短期记忆和长期记忆，提供简洁的接口。
"""
from typing import Any, Dict, List, Optional
from .base import MemoryItem
from .short_term import ShortTermMemory
from .long_term import LongTermMemory


class MemoryManager:
    """Memory 管理器"""

    def __init__(self, storage_path: str = "data/memory"):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(storage_path)

    # 会话管理 (短期记忆)
    def add_message(self, role: str, content: str, metadata: Dict = None) -> None:
        """添加对话消息"""
        self.short_term.add_message(role, content, metadata)

    def get_conversation(self, limit: int = None) -> List[Dict]:
        """获取对话历史"""
        return self.short_term.get_messages(limit)

    def get_context_for_api(self) -> List[Dict]:
        """获取用于 API 调用的上下文"""
        return self.short_term.get_context_window()

    def set_session_context(self, key: str, value: Any) -> None:
        """设置会话上下文"""
        self.short_term.set_context(key, value)

    def get_session_context(self, key: str, default: Any = None) -> Any:
        """获取会话上下文"""
        return self.short_term.get_context(key, default)

    def clear_session(self) -> None:
        """清空当前会话"""
        self.short_term.clear()

    # 用户数据 (长期记忆)
    def save_user(self, user_id: str, profile: Dict) -> None:
        """保存用户数据"""
        self.long_term.save_user_profile(user_id, profile)
        # 同时设置到会话上下文
        self.set_session_context("user_id", user_id)
        self.set_session_context("user_profile", profile)

    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户数据"""
        return self.long_term.get_user_profile(user_id)

    def save_workout(self, user_id: str, workout: Dict) -> None:
        """保存训练记录"""
        self.long_term.save_workout_history(user_id, workout)

    def get_workout_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取训练历史"""
        return self.long_term.get_workout_history(user_id, limit)

    def save_body_record(self, user_id: str, data: Dict) -> None:
        """保存身体数据"""
        self.long_term.save_body_data(user_id, data)

    def get_body_history(self, user_id: str, limit: int = 30) -> List[Dict]:
        """获取身体数据历史"""
        return self.long_term.get_body_data_history(user_id, limit)

    # 综合信息获取
    def get_user_context(self, user_id: str) -> Dict:
        """获取用户的完整上下文 (用于 AI)"""
        profile = self.get_user(user_id) or {}
        recent_workouts = self.get_workout_history(user_id, 5)
        body_history = self.get_body_history(user_id, 10)

        return {
            "user_profile": profile,
            "recent_workouts": recent_workouts,
            "body_progress": body_history,
            "session_context": self.short_term.get_full_context()
        }

    # 搜索
    def search_memory(self, query: str, search_long_term: bool = True) -> List[MemoryItem]:
        """搜索记忆"""
        results = self.short_term.search(query)
        if search_long_term:
            results.extend(self.long_term.search(query))
        return results

    # 统计
    def get_stats(self) -> Dict:
        """获取记忆统计"""
        return {
            "short_term": {
                "message_count": self.short_term.message_count
            },
            "long_term": self.long_term.get_stats()
        }
