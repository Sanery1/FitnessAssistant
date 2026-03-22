"""
Short-term memory (Conversation context)

管理当前会话的上下文记忆，包括对话历史、临时状态等。
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
from .base import BaseMemory, MemoryItem


class ConversationMessage:
    """对话消息"""
    def __init__(self, role: str, content: str, metadata: Dict = None):
        self.role = role  # "user" | "assistant" | "system"
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class ShortTermMemory(BaseMemory):
    """短期记忆 - 会话上下文"""

    def __init__(
        self,
        max_messages: int = 50,
        max_tokens: int = 4000,
        context_window: int = 10
    ):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.context_window = context_window

        # 使用双端队列存储消息，自动限制长度
        self._messages: deque = deque(maxlen=max_messages)
        self._context: Dict[str, Any] = {}
        self._temp_data: Dict[str, Any] = {}

    def add_message(self, role: str, content: str, metadata: Dict = None) -> None:
        """添加对话消息"""
        msg = ConversationMessage(role, content, metadata)
        self._messages.append(msg)

    def get_messages(self, limit: int = None) -> List[Dict]:
        """获取对话消息 (Claude API 格式)"""
        messages = list(self._messages)
        if limit:
            messages = messages[-limit:]

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def get_context_window(self) -> List[Dict]:
        """获取上下文窗口内的消息"""
        return self.get_messages(self.context_window)

    # BaseMemory 接口实现
    def add(self, item: MemoryItem) -> None:
        """添加记忆项"""
        if isinstance(item.content, dict):
            if "role" in item.content and "content" in item.content:
                self.add_message(
                    item.content["role"],
                    item.content["content"],
                    item.metadata
                )
                return
        # 存储为临时数据
        key = f"item_{len(self._temp_data)}"
        self._temp_data[key] = item

    def get(self, key: str) -> Optional[MemoryItem]:
        """获取记忆"""
        return self._temp_data.get(key)

    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        return list(self._temp_data.values())

    def clear(self) -> None:
        """清空记忆"""
        self._messages.clear()
        self._context.clear()
        self._temp_data.clear()

    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """简单关键词搜索"""
        results = []
        query_lower = query.lower()

        for msg in self._messages:
            if query_lower in msg.content.lower():
                results.append(MemoryItem(
                    content={"role": msg.role, "content": msg.content},
                    metadata=msg.metadata,
                    created_at=msg.timestamp
                ))
                if len(results) >= limit:
                    break

        return results

    # 上下文管理
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self._context.get(key, default)

    def get_full_context(self) -> Dict[str, Any]:
        """获取完整上下文"""
        return {
            "messages": self.get_messages(),
            "context": self._context.copy(),
            "temp_data": {k: v for k, v in self._temp_data.items()}
        }

    # 统计信息
    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def has_messages(self) -> bool:
        return len(self._messages) > 0

    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息"""
        for msg in reversed(self._messages):
            if msg.role == "user":
                return msg.content
        return None

    def summarize_for_context(self) -> str:
        """生成上下文摘要 (用于注入到 prompt)"""
        if not self._context:
            return ""

        lines = ["当前会话上下文:"]
        for key, value in self._context.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)
