"""
Tools module
"""
from .base import Tool, ToolResult, ToolRegistry, registry, tool
from .workout_tools import GenerateWorkoutPlanTool, GetExerciseInfoTool
from .nutrition_tools import CalculateCaloriesTool, AnalyzeNutritionTool
from .body_tools import CalculateBMITool, TrackBodyProgressTool, CalculateBodyFatTool

__all__ = [
    # Base
    "Tool", "ToolResult", "ToolRegistry", "registry", "tool",
    # Workout
    "GenerateWorkoutPlanTool", "GetExerciseInfoTool",
    # Nutrition
    "CalculateCaloriesTool", "AnalyzeNutritionTool",
    # Body
    "CalculateBMITool", "TrackBodyProgressTool", "CalculateBodyFatTool",
]


def get_all_tool_schemas():
    """获取所有工具的 Claude API schema"""
    return registry.get_all_schemas()


def execute_tool(name: str, **kwargs) -> ToolResult:
    """执行指定工具"""
    return registry.execute(name, **kwargs)
