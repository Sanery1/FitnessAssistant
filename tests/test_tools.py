"""
Tests for Tool System
"""
import sys
sys.path.insert(0, ".")

from src.tools import registry
from src.tools.base import ToolResult


def test_registry():
    """测试工具注册中心"""
    tools = registry.list_tools()
    print("已注册工具:", tools)
    assert "generate_workout_plan" in tools
    assert "calculate_calories" in tools
    assert "calculate_bmi" in tools
    print("✅ 注册中心测试通过")


def test_workout_tool():
    """测试训练计划生成工具"""
    result = registry.execute(
        "generate_workout_plan",
        goal="减脂",
        level="初学者",
        days_per_week=3,
        minutes_per_day=60
    )

    assert result.success
    assert "name" in result.data
    assert "sessions" in result.data
    assert len(result.data["sessions"]) == 3
    print("✅ 训练计划生成测试通过")
    print(f"   计划名称: {result.data['name']}")
    print(f"   训练次数: {len(result.data['sessions'])} 次/周")


def test_nutrition_tool():
    """测试热量计算工具"""
    result = registry.execute(
        "calculate_calories",
        gender="男",
        age=28,
        height=175,
        weight=70,
        activity_level="中度活动",
        goal="减脂"
    )

    assert result.success
    assert "bmr" in result.data
    assert "target_calories" in result.data
    assert "macros" in result.data
    print("✅ 热量计算测试通过")
    print(f"   基础代谢: {result.data['bmr']} kcal")
    print(f"   目标热量: {result.data['target_calories']} kcal")


def test_bmi_tool():
    """测试 BMI 计算工具"""
    result = registry.execute(
        "calculate_bmi",
        height=175,
        weight=70
    )

    assert result.success
    assert "bmi" in result.data
    assert "category" in result.data
    print("✅ BMI 计算测试通过")
    print(f"   BMI: {result.data['bmi']}")
    print(f"   分类: {result.data['category']}")


def test_exercise_info():
    """测试动作信息工具"""
    result = registry.execute(
        "get_exercise_info",
        exercise_name="深蹲"
    )

    assert result.success
    assert "name" in result.data
    print("✅ 动作信息测试通过")
    print(f"   动作: {result.data['name']}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("🧪 工具系统测试")
    print("=" * 50 + "\n")

    test_registry()
    test_workout_tool()
    test_nutrition_tool()
    test_bmi_tool()
    test_exercise_info()

    print("\n" + "=" * 50)
    print("✅ 所有工具测试通过!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
