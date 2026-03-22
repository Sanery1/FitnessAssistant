"""
Agent Base Classes

定义 Agent 基础架构，支持工具调用、记忆管理、消息处理。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field
import json


class AgentRole(str, Enum):
    """Agent 角色"""
    ORCHESTRATOR = "orchestrator"  # 主控编排
    FITNESS_COACH = "fitness_coach"  # 健身教练
    NUTRITIONIST = "nutritionist"  # 营养师
    DATA_ANALYST = "data_analyst"  # 数据分析师
    ASSISTANT = "assistant"  # 通用助手


class AgentState(str, Enum):
    """Agent 状态"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


class AgentMessage(BaseModel):
    """Agent 消息"""
    role: str = Field(description="角色: user/assistant/tool/system")
    content: str = Field(description="消息内容")
    name: Optional[str] = Field(default=None, description="工具名称(仅tool角色)")
    tool_call_id: Optional[str] = Field(default=None, description="工具调用ID")


class ToolCall(BaseModel):
    """工具调用"""
    id: str = Field(description="调用ID")
    name: str = Field(description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="参数")


class AgentResponse(BaseModel):
    """Agent 响应"""
    content: str = Field(default="", description="文本内容")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="工具调用")
    done: bool = Field(default=True, description="是否完成")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(
        self,
        name: str,
        role: AgentRole,
        llm_client: Any = None,
        tools: List[Any] = None,
        memory: Any = None
    ):
        self.name = name
        self.role = role
        self.llm = llm_client
        self.tools = tools or []
        self.memory = memory
        self.state = AgentState.IDLE
        self.conversation: List[AgentMessage] = []

    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass

    @abstractmethod
    def process(self, message: str, context: Dict = None) -> AgentResponse:
        """处理消息"""
        pass

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """添加消息到历史"""
        self.conversation.append(AgentMessage(role=role, content=content, **kwargs))

    def get_messages_for_api(self) -> List[Dict]:
        """获取 API 格式的消息"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation
            if msg.role != "tool"  # OpenAI 格式不包含 tool 角色消息
        ]

    def clear_conversation(self) -> None:
        """清空对话"""
        self.conversation = []

    def get_tool_schemas(self) -> List[Dict]:
        """获取工具定义"""
        if hasattr(self.tools, 'get_all_schemas'):
            return self.tools.get_all_schemas(openai_format=True)
        return [t.get_openai_schema() for t in self.tools if hasattr(t, 'get_openai_schema')]

    def execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """执行工具"""
        if hasattr(self.tools, 'execute'):
            result = self.tools.execute(tool_name, **arguments)
            return result.to_string() if hasattr(result, 'to_string') else str(result.data)

        for tool in self.tools:
            if hasattr(tool, 'name') and tool.name == tool_name:
                result = tool.execute(**arguments)
                return result.to_string() if hasattr(result, 'to_string') else str(result.data)

        return f"工具 '{tool_name}' 不存在"


class ToolExecutor:
    """工具执行器"""

    def __init__(self, tool_registry: Any):
        self.registry = tool_registry

    def execute(self, tool_call: ToolCall) -> str:
        """执行工具调用"""
        try:
            result = self.registry.execute(tool_call.name, **tool_call.arguments)
            if hasattr(result, 'to_string'):
                return result.to_string()
            return json.dumps(result.data, ensure_ascii=False) if result.success else f"错误: {result.error}"
        except Exception as e:
            return f"执行错误: {str(e)}"

    def execute_batch(self, tool_calls: List[ToolCall]) -> Dict[str, str]:
        """批量执行工具"""
        results = {}
        for tc in tool_calls:
            results[tc.id] = self.execute(tc)
        return results
