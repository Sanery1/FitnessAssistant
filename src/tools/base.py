"""
Tool system for Function Calling

支持 OpenAI/GLM 兼容的工具调用机制，定义工具基类和注册系统。
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
import json


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool = Field(description="是否成功")
    data: Any = Field(default=None, description="返回数据")
    error: Optional[str] = Field(default=None, description="错误信息")

    def to_string(self) -> str:
        """转换为字符串供AI理解"""
        if self.success:
            return json.dumps(self.data, ensure_ascii=False, default=str)
        return f"错误: {self.error}"


class Tool(ABC):
    """工具基类"""

    name: str = "base_tool"
    description: str = "基础工具"
    parameters_schema: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """获取 OpenAI/GLM API 工具定义"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters_schema,
                "required": [k for k, v in self.parameters_schema.items()
                            if v.get("required", False)]
            }
        }

    def get_openai_schema(self) -> Dict[str, Any]:
        """获取 OpenAI 格式的工具定义"""
        return {
            "type": "function",
            "function": self.get_schema()
        }


class ToolRegistry:
    """工具注册中心"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Tool] = {}
        return cls._instance

    def register(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具名"""
        return list(self._tools.keys())

    def get_all_schemas(self, openai_format: bool = True) -> List[Dict[str, Any]]:
        """获取所有工具的 API schema"""
        if openai_format:
            return [tool.get_openai_schema() for tool in self._tools.values()]
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> ToolResult:
        """执行指定工具"""
        tool = self.get(name)
        if tool is None:
            return ToolResult(success=False, error=f"工具 '{name}' 不存在")
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# 全局工具注册中心
registry = ToolRegistry()


def tool(name: str, description: str, parameters: Dict[str, Any]):
    """工具装饰器，用于快速定义工具"""
    def decorator(func: Callable) -> Tool:
        class FunctionTool(Tool):
            def __init__(self):
                self.name = name
                self.description = description
                self.parameters_schema = parameters

            def execute(self, **kwargs) -> ToolResult:
                result = func(**kwargs)
                if isinstance(result, ToolResult):
                    return result
                return ToolResult(success=True, data=result)

        tool_instance = FunctionTool()
        registry.register(tool_instance)
        return tool_instance
    return decorator
