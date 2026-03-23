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
    print("Registered tools:", tools)
    assert "generate_workout_plan" in tools
    assert "calculate_calories" in tools
    assert "calculate_bmi" in tools
    print("[PASS] Registry test passed")


def test_workout_tool():
    """测试训练计划生成工具"""
    result = registry.execute(
        "generate_workout_plan",
        goal="fat_loss",
        level="beginner",
        days_per_week=3,
        minutes_per_day=60
    )

    assert result.success
    assert "name" in result.data
    assert "sessions" in result.data
    assert len(result.data["sessions"]) == 3
    print("[PASS] Workout plan generation test passed")
    print(f"   Plan name: {result.data['name']}")
    print(f"   Sessions per week: {len(result.data['sessions'])}")


def test_nutrition_tool():
    """测试热量计算工具"""
    result = registry.execute(
        "calculate_calories",
        gender="male",
        age=28,
        height=175,
        weight=70,
        activity_level="moderate",
        goal="lose_weight"
    )

    assert result.success
    assert "bmr" in result.data
    assert "target_calories" in result.data
    assert "macros" in result.data
    print("[PASS] Calorie calculation test passed")
    print(f"   BMR: {result.data['bmr']} kcal")
    print(f"   Target calories: {result.data['target_calories']} kcal")


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
    print("[PASS] BMI calculation test passed")
    print(f"   BMI: {result.data['bmi']}")
    print(f"   Category: {result.data['category']}")


def test_exercise_info():
    """测试动作信息工具"""
    result = registry.execute(
        "get_exercise_info",
        exercise_name="squat"
    )

    assert result.success
    assert "name" in result.data
    print("[PASS] Exercise info test passed")
    print(f"   Exercise: {result.data['name']}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("Tool System Tests")
    print("=" * 50 + "\n")

    test_registry()
    test_workout_tool()
    test_nutrition_tool()
    test_bmi_tool()
    test_exercise_info()

    print("\n" + "=" * 50)
    print("All Tool Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
