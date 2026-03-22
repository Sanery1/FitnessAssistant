"""
Memory system base classes

实现短期记忆(会话上下文)和长期记忆(用户数据持久化)管理。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """记忆项"""
    content: Any = Field(description="记忆内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    importance: float = Field(default=0.5, ge=0, le=1, description="重要程度 0-1")


class BaseMemory(ABC):
    """Memory 基类"""

    @abstractmethod
    def add(self, item: MemoryItem) -> None:
        """添加记忆"""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[MemoryItem]:
        """获取记忆"""
        pass

    @abstractmethod
    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空记忆"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索记忆"""
        pass
