"""
FastAPI Routes - Workout
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...tools import registry
from ...memory import MemoryManager
from ...config import settings


router = APIRouter(prefix="/workout", tags=["workout"])

_memory: Optional[MemoryManager] = None


def get_memory() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager(settings.memory_path)
    return _memory


# 请求模型
class GeneratePlanRequest(BaseModel):
    goal: str
    level: str
    days_per_week: int
    minutes_per_day: int
    focus_areas: Optional[List[str]] = None
    injuries: Optional[List[str]] = None
    user_id: Optional[str] = None


class ExerciseInfoRequest(BaseModel):
    exercise_name: str


class SaveWorkoutRequest(BaseModel):
    user_id: str
    workout: Dict[str, Any]


@router.post("/generate-plan")
async def generate_plan(request: GeneratePlanRequest):
    """生成训练计划"""
    result = registry.execute(
        "generate_workout_plan",
        goal=request.goal,
        level=request.level,
        days_per_week=request.days_per_week,
        minutes_per_day=request.minutes_per_day,
        focus_areas=request.focus_areas or [],
        injuries=request.injuries or []
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/exercise-info")
async def get_exercise_info(request: ExerciseInfoRequest):
    """获取动作详情"""
    result = registry.execute("get_exercise_info", exercise_name=request.exercise_name)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/save")
async def save_workout(request: SaveWorkoutRequest):
    """保存训练记录"""
    memory = get_memory()
    workout_data = request.workout
    workout_data["saved_at"] = datetime.now().isoformat()

    memory.save_workout(request.user_id, workout_data)

    return {"success": True, "message": "训练记录已保存"}


@router.get("/history/{user_id}")
async def get_workout_history(user_id: str, limit: int = 10):
    """获取训练历史"""
    memory = get_memory()
    history = memory.get_workout_history(user_id, limit)
    return {"user_id": user_id, "history": history}
