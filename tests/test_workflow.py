"""
Tests for Workflow System
"""
import sys
import asyncio
import inspect
sys.path.insert(0, ".")

from src.workflow import (
    WorkflowGraph, WorkflowExecutor, WorkflowManager,
    FunctionNode, ToolNode, WorkflowState
)
from src.tools import registry


def test_workflow_graph():
    """测试工作流图"""
    print("\n[INFO] Workflow graph test")

    graph = WorkflowGraph("test_workflow", "Test Workflow")

    # 添加节点
    def step1(ctx, state):
        return {"result": "step1 done"}

    def step2(ctx, state):
        return {"result": "step2 done"}

    graph.add_node(FunctionNode("step1", "Step 1", step1))
    graph.add_node(FunctionNode("step2", "Step 2", step2, dependencies=["step1"]))

    # 添加边
    graph.add_edge("step1", "step2")
    graph.set_entry("step1")

    # 拓扑排序
    order = graph.topological_sort()
    assert order == ["step1", "step2"]

    # 可视化
    print(graph.visualize())

    print("[PASS] Workflow graph test passed")


def test_workflow_state():
    """测试工作流状态"""
    print("\n[INFO] Workflow state test")

    state = WorkflowState(
        workflow_id="test",
        name="Test"
    )

    state.start()
    assert state.status == "running"

    state.set_node_running("node1")
    assert state.current_node == "node1"

    state.set_node_completed("node1", {"data": "result"})
    assert "node1" in state.completed_nodes
    assert state.results["node1"]["data"] == "result"

    print(f"   Progress: {state.progress * 100:.0f}%")
    print("[PASS] Workflow state test passed")


async def test_workflow_executor():
    """测试工作流执行器"""
    print("\n[INFO] Workflow executor test")

    # 创建工作流
    graph = WorkflowGraph("exec_test", "Executor Test")

    async def async_step1(ctx, state):
        await asyncio.sleep(0.1)
        return {"value": 100}

    async def async_step2(ctx, state):
        prev = ctx.get("step1_result", {})
        return {"value": prev.get("value", 0) * 2}

    graph.add_node(FunctionNode("step1", "Step 1", async_step1))
    graph.add_node(FunctionNode("step2", "Step 2", async_step2, dependencies=["step1"]))
    graph.add_edge("step1", "step2")
    graph.set_entry("step1")

    # 执行
    executor = WorkflowExecutor(graph)
    final_state = await executor.run({"initial": True})

    assert final_state.status == "completed"
    assert final_state.results["step1"]["value"] == 100
    assert final_state.results["step2"]["value"] == 200
    assert not inspect.iscoroutine(final_state.results["step1"])
    assert not inspect.iscoroutine(final_state.results["step2"])
    print(f"   Final status: {final_state.status}")
    print(f"   Results: {final_state.results}")

    print("[PASS] Workflow executor test passed")


def test_workflow_manager():
    """测试工作流管理器"""
    print("\n[INFO] Workflow manager test")

    manager = WorkflowManager()

    # 注册工作流
    graph = WorkflowGraph("managed", "Managed Workflow")
    graph.add_node(FunctionNode("node1", "Node 1", lambda c, s: {"ok": True}))
    graph.set_entry("node1")

    manager.register(graph)

    executor = manager.create_executor("managed")
    assert executor is not None
    assert "managed" in manager.executors

    # 列出
    workflows = manager.list_workflows()
    assert len(workflows) == 1

    print(f"   Registered workflows: {workflows}")
    print("[PASS] Workflow manager test passed")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("Workflow System Tests")
    print("=" * 50)

    test_workflow_graph()
    test_workflow_state()
    asyncio.run(test_workflow_executor())
    test_workflow_manager()

    print("\n" + "=" * 50)
    print("All Workflow Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
