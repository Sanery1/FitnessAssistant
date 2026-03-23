"""
Workflow Nodes

工作流节点定义，每个节点执行特定的任务。
"""
from abc import ABC, abstractmethod
import inspect
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field


class NodeResult(BaseModel):
    """节点执行结果"""
    success: bool = Field(description="是否成功")
    data: Any = Field(default=None, description="返回数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    next_node: Optional[str] = Field(default=None, description="指定下一个节点")


class WorkflowNode(ABC):
    """工作流节点基类"""

    def __init__(
        self,
        node_id: str,
        name: str,
        description: str = "",
        dependencies: List[str] = None
    ):
        self.node_id = node_id
        self.name = name
        self.description = description
        self.dependencies = dependencies or []

    @abstractmethod
    async def execute(self, context: Dict[str, Any], state: Any) -> NodeResult:
        """执行节点"""
        pass

    def can_execute(self, completed_nodes: List[str]) -> bool:
        """检查是否可以执行"""
        return all(dep in completed_nodes for dep in self.dependencies)


class FunctionNode(WorkflowNode):
    """函数节点 - 包装普通函数为节点"""

    def __init__(
        self,
        node_id: str,
        name: str,
        func: Callable,
        dependencies: List[str] = None
    ):
        super().__init__(node_id, name, dependencies=dependencies)
        self.func = func

    async def execute(self, context: Dict[str, Any], state: Any) -> NodeResult:
        """执行函数"""
        try:
            result = self.func(context, state)
            if inspect.isawaitable(result):
                result = await result
            return NodeResult(success=True, data=result)
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class AgentNode(WorkflowNode):
    """Agent 节点 - 调用 Agent 处理"""

    def __init__(
        self,
        node_id: str,
        name: str,
        agent: Any,
        dependencies: List[str] = None
    ):
        super().__init__(node_id, name, dependencies=dependencies)
        self.agent = agent

    async def execute(self, context: Dict[str, Any], state: Any) -> NodeResult:
        """调用 Agent"""
        try:
            message = context.get("message", "")
            response = self.agent.process(message, context)
            return NodeResult(success=True, data=response.content)
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class ToolNode(WorkflowNode):
    """工具节点 - 调用工具执行"""

    def __init__(
        self,
        node_id: str,
        name: str,
        tool_name: str,
        tool_registry: Any,
        dependencies: List[str] = None
    ):
        super().__init__(node_id, name, dependencies=dependencies)
        self.tool_name = tool_name
        self.tool_registry = tool_registry

    async def execute(self, context: Dict[str, Any], state: Any) -> NodeResult:
        """执行工具"""
        try:
            # 从上下文获取参数
            args = context.get("tool_args", {})
            result = self.tool_registry.execute(self.tool_name, **args)

            return NodeResult(
                success=result.success,
                data=result.data if result.success else None,
                error=result.error if not result.success else None
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class ConditionNode(WorkflowNode):
    """条件节点 - 根据条件分支"""

    def __init__(
        self,
        node_id: str,
        name: str,
        condition: Callable[[Dict], bool],
        true_node: str,
        false_node: str,
        dependencies: List[str] = None
    ):
        super().__init__(node_id, name, dependencies=dependencies)
        self.condition = condition
        self.true_node = true_node
        self.false_node = false_node

    async def execute(self, context: Dict[str, Any], state: Any) -> NodeResult:
        """执行条件判断"""
        try:
            result = self.condition(context)
            next_node = self.true_node if result else self.false_node
            return NodeResult(success=True, data=result, next_node=next_node)
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class ParallelNode(WorkflowNode):
    """并行节点 - 并行执行多个节点"""

    def __init__(
        self,
        node_id: str,
        name: str,
        nodes: List[WorkflowNode],
        dependencies: List[str] = None
    ):
        super().__init__(node_id, name, dependencies=dependencies)
        self.nodes = nodes

    async def execute(self, context: Dict[str, Any], state: Any) -> NodeResult:
        """并行执行所有子节点"""
        import asyncio

        tasks = [node.execute(context, state) for node in self.nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = all(r.success if isinstance(r, NodeResult) else False for r in results)
        data = {
            node.node_id: r.data if isinstance(r, NodeResult) else str(r)
            for node, r in zip(self.nodes, results)
        }

        return NodeResult(success=success, data=data)
