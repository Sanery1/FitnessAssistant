"""
Workflow Executor

工作流执行引擎，负责执行工作流图。
"""
from typing import Any, Dict, Optional
import asyncio

from .graph import WorkflowGraph
from .state import WorkflowState, WorkflowStatus
from .nodes import NodeResult


class WorkflowExecutor:
    """工作流执行器"""

    def __init__(self, graph: WorkflowGraph):
        self.graph = graph
        self.state: Optional[WorkflowState] = None

    def start(self, initial_context: Dict[str, Any] = None) -> WorkflowState:
        """开始执行工作流"""
        self.state = self.graph.create_state()
        self.state.context = initial_context or {}
        self.state.start()

        return self.state

    async def run(self, initial_context: Dict[str, Any] = None) -> WorkflowState:
        """异步执行整个工作流"""
        self.start(initial_context)

        # 获取执行顺序
        order = self.graph.topological_sort()

        for node_id in order:
            if self.state.status == WorkflowStatus.FAILED:
                break

            await self.execute_node(node_id)

        if self.state.status == WorkflowStatus.RUNNING:
            self.state.complete()

        return self.state

    async def execute_node(self, node_id: str) -> NodeResult:
        """执行单个节点"""
        node = self.graph.nodes.get(node_id)
        if not node:
            return NodeResult(success=False, error=f"节点 {node_id} 不存在")

        # 检查依赖
        if not node.can_execute(self.state.completed_nodes):
            self.state.skip_node(node_id)
            return NodeResult(success=True, data="跳过: 依赖未满足")

        # 设置运行状态
        self.state.set_node_running(node_id)

        # 执行节点
        result = await node.execute(self.state.context, self.state)

        # 更新状态
        if result.success:
            self.state.set_node_completed(node_id, result.data)
            # 将结果存入上下文
            self.state.context[f"{node_id}_result"] = result.data
        else:
            self.state.set_node_failed(node_id, result.error)

        return result

    def pause(self) -> None:
        """暂停工作流"""
        if self.state:
            self.state.status = WorkflowStatus.PAUSED

    def resume(self) -> None:
        """恢复工作流"""
        if self.state and self.state.status == WorkflowStatus.PAUSED:
            self.state.status = WorkflowStatus.RUNNING

    def get_state(self) -> Optional[WorkflowState]:
        """获取当前状态"""
        return self.state

    def get_progress(self) -> float:
        """获取进度"""
        return self.state.progress if self.state else 0.0


class WorkflowManager:
    """工作流管理器 - 管理多个工作流实例"""

    def __init__(self):
        self.workflows: Dict[str, WorkflowGraph] = {}
        self.executors: Dict[str, WorkflowExecutor] = {}

    def register(self, graph: WorkflowGraph) -> None:
        """注册工作流"""
        self.workflows[graph.workflow_id] = graph

    def create_executor(self, workflow_id: str) -> WorkflowExecutor:
        """创建执行器"""
        graph = self.workflows.get(workflow_id)
        if not graph:
            raise ValueError(f"工作流 {workflow_id} 不存在")

        executor = WorkflowExecutor(graph)
        self.executors[workflow_id] = executor
        return executor

    async def run_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> WorkflowState:
        """运行工作流"""
        executor = self.create_executor(workflow_id)
        return await executor.run(context)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowGraph]:
        """获取工作流定义"""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> list:
        """列出所有工作流"""
        return [
            {"id": wf.workflow_id, "name": wf.name}
            for wf in self.workflows.values()
        ]
