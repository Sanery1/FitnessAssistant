"""
Workflow Graph

工作流图，定义节点之间的连接关系。
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict

from .nodes import WorkflowNode
from .state import WorkflowState


class WorkflowGraph:
    """工作流图"""

    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)
        self.entry_node: Optional[str] = None

    def add_node(self, node: WorkflowNode) -> "WorkflowGraph":
        """添加节点"""
        self.nodes[node.node_id] = node
        return self

    def add_edge(self, from_node: str, to_node: str) -> "WorkflowGraph":
        """添加边 (连接)"""
        if from_node not in self.nodes:
            raise ValueError(f"节点 {from_node} 不存在")
        if to_node not in self.nodes:
            raise ValueError(f"节点 {to_node} 不存在")

        self.edges[from_node].append(to_node)
        return self

    def set_entry(self, node_id: str) -> "WorkflowGraph":
        """设置入口节点"""
        if node_id not in self.nodes:
            raise ValueError(f"节点 {node_id} 不存在")
        self.entry_node = node_id
        return self

    def get_next_nodes(self, node_id: str) -> List[str]:
        """获取下一个节点列表"""
        return self.edges.get(node_id, [])

    def get_dependencies(self, node_id: str) -> List[str]:
        """获取节点的依赖 (入边)"""
        deps = []
        for from_node, to_nodes in self.edges.items():
            if node_id in to_nodes:
                deps.append(from_node)
        return deps

    def topological_sort(self) -> List[str]:
        """拓扑排序，获取执行顺序"""
        in_degree = {node: 0 for node in self.nodes}

        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                in_degree[to_node] += 1

        # 入度为0的节点
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for next_node in self.edges.get(node, []):
                in_degree[next_node] -= 1
                if in_degree[next_node] == 0:
                    queue.append(next_node)

        return result

    def create_state(self) -> WorkflowState:
        """创建工作流状态"""
        state = WorkflowState(
            workflow_id=self.workflow_id,
            name=self.name
        )

        # 初始化所有节点状态
        for node_id in self.nodes:
            state.node_states[node_id] = "pending"

        return state

    def visualize(self) -> str:
        """生成可视化文本"""
        lines = [f"工作流: {self.name}", "=" * 40]

        order = self.topological_sort()
        for i, node_id in enumerate(order):
            node = self.nodes[node_id]
            next_nodes = self.get_next_nodes(node_id)

            prefix = "└─" if i == len(order) - 1 else "├─"
            lines.append(f"{prefix} [{node_id}] {node.name}")

            for j, next_id in enumerate(next_nodes):
                sub_prefix = "    └─" if j == len(next_nodes) - 1 else "    ├─"
                lines.append(f"{sub_prefix} → {next_id}")

        return "\n".join(lines)


# 预定义的工作流模板
def create_workout_plan_workflow(tool_registry: Any) -> WorkflowGraph:
    """创建训练计划生成工作流"""
    from .nodes import ToolNode

    graph = WorkflowGraph("workout_plan", "训练计划生成")

    # 添加节点
    graph.add_node(ToolNode(
        "calc_bmi", "计算BMI", "calculate_bmi", tool_registry
    ))
    graph.add_node(ToolNode(
        "calc_calories", "计算热量", "calculate_calories", tool_registry,
        dependencies=["calc_bmi"]
    ))
    graph.add_node(ToolNode(
        "generate_plan", "生成计划", "generate_workout_plan", tool_registry,
        dependencies=["calc_calories"]
    ))

    # 添加边
    graph.add_edge("calc_bmi", "calc_calories")
    graph.add_edge("calc_calories", "generate_plan")

    # 设置入口
    graph.set_entry("calc_bmi")

    return graph
