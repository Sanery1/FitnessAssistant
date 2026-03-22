"""
Workflow State Management

工作流状态机，管理多步骤任务的执行状态。
"""
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SKIPPED = "skipped"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowState(BaseModel):
    """工作流状态"""
    workflow_id: str = Field(description="工作流ID")
    name: str = Field(description="工作流名称")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="整体状态")
    current_node: Optional[str] = Field(default=None, description="当前节点")
    completed_nodes: List[str] = Field(default_factory=list, description="已完成节点")
    node_states: Dict[str, NodeStatus] = Field(default_factory=dict, description="节点状态")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    results: Dict[str, Any] = Field(default_factory=dict, description="节点结果")
    errors: Dict[str, str] = Field(default_factory=dict, description="错误信息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

    def start(self) -> None:
        """开始工作流"""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self) -> None:
        """完成工作流"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """工作流失败"""
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.now()
        if self.current_node:
            self.errors[self.current_node] = error

    def set_node_running(self, node_id: str) -> None:
        """设置节点运行中"""
        self.current_node = node_id
        self.node_states[node_id] = NodeStatus.RUNNING

    def set_node_completed(self, node_id: str, result: Any = None) -> None:
        """设置节点完成"""
        self.node_states[node_id] = NodeStatus.COMPLETED
        self.completed_nodes.append(node_id)
        if result is not None:
            self.results[node_id] = result
        self.current_node = None

    def set_node_failed(self, node_id: str, error: str) -> None:
        """设置节点失败"""
        self.node_states[node_id] = NodeStatus.FAILED
        self.errors[node_id] = error
        self.fail(error)

    def skip_node(self, node_id: str) -> None:
        """跳过节点"""
        self.node_states[node_id] = NodeStatus.SKIPPED

    @property
    def progress(self) -> float:
        """计算进度"""
        if not self.node_states:
            return 0.0
        completed = sum(1 for s in self.node_states.values()
                       if s in [NodeStatus.COMPLETED, NodeStatus.SKIPPED])
        return completed / len(self.node_states)
