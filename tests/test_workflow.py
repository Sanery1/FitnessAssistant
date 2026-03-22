"""
Tests for Workflow System
"""
import sys
import asyncio
sys.path.insert(0, ".")

from src.workflow import (
    WorkflowGraph, WorkflowExecutor, WorkflowManager,
    FunctionNode, ToolNode, WorkflowState
)
from src.tools import registry


def test_workflow_graph():
    """测试工作流图"""
    print("\n📊 工作流图测试")

    graph = WorkflowGraph("test_workflow", "测试工作流")

    # 添加节点
    def step1(ctx, state):
        return {"result": "step1 done"}

    def step2(ctx, state):
        return {"result": "step2 done"}

    graph.add_node(FunctionNode("step1", "步骤1", step1))
    graph.add_node(FunctionNode("step2", "步骤2", step2, dependencies=["step1"]))

    # 添加边
    graph.add_edge("step1", "step2")
    graph.set_entry("step1")

    # 拓扑排序
    order = graph.topological_sort()
    assert order == ["step1", "step2"]

    # 可视化
    print(graph.visualize())

    print("✅ 工作流图测试通过")


def test_workflow_state():
    """测试工作流状态"""
    print("\n📈 工作流状态测试")

    state = WorkflowState(
        workflow_id="test",
        name="测试"
    )

    state.start()
    assert state.status == "running"

    state.set_node_running("node1")
    assert state.current_node == "node1"

    state.set_node_completed("node1", {"data": "result"})
    assert "node1" in state.completed_nodes
    assert state.results["node1"]["data"] == "result"

    print(f"   进度: {state.progress * 100:.0f}%")
    print("✅ 工作流状态测试通过")


async def test_workflow_executor():
    """测试工作流执行器"""
    print("\n⚡ 工作流执行器测试")

    # 创建工作流
    graph = WorkflowGraph("exec_test", "执行测试")

    async def async_step1(ctx, state):
        await asyncio.sleep(0.1)
        return {"value": 100}

    async def async_step2(ctx, state):
        prev = ctx.get("step1_result", {})
        return {"value": prev.get("value", 0) * 2}

    graph.add_node(FunctionNode("step1", "步骤1", async_step1))
    graph.add_node(FunctionNode("step2", "步骤2", async_step2, dependencies=["step1"]))
    graph.add_edge("step1", "step2")
    graph.set_entry("step1")

    # 执行
    executor = WorkflowExecutor(graph)
    final_state = await executor.run({"initial": True})

    assert final_state.status == "completed"
    print(f"   最终状态: {final_state.status}")
    print(f"   结果: {final_state.results}")

    print("✅ 工作流执行器测试通过")


def test_workflow_manager():
    """测试工作流管理器"""
    print("\n🗂️ 工作流管理器测试")

    manager = WorkflowManager()

    # 注册工作流
    graph = WorkflowGraph("managed", "管理工作流")
    graph.add_node(FunctionNode("node1", "节点1", lambda c, s: {"ok": True}))
    graph.set_entry("node1")

    manager.register(graph)

    # 列出
    workflows = manager.list_workflows()
    assert len(workflows) == 1

    print(f"   已注册工作流: {workflows}")
    print("✅ 工作流管理器测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("🧪 工作流系统测试")
    print("=" * 50)

    test_workflow_graph()
    test_workflow_state()
    asyncio.run(test_workflow_executor())
    test_workflow_manager()

    print("\n" + "=" * 50)
    print("✅ 所有工作流测试通过!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
