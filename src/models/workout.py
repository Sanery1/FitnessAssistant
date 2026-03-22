"""
Workout related models
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class MuscleGroup(str, Enum):
    """肌群"""
    CHEST = "胸肌"
    BACK = "背部"
    SHOULDERS = "肩部"
    ARMS = "手臂"
    LEGS = "腿部"
    CORE = "核心"
    FULL_BODY = "全身"
    CARDIO = "有氧"


class ExerciseType(str, Enum):
    """运动类型"""
    STRENGTH = "力量训练"
    CARDIO = "有氧运动"
    FLEXIBILITY = "柔韧性"
    HIIT = "高强度间歇"
    RECOVERY = "恢复训练"


class Difficulty(str, Enum):
    """难度"""
    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"
    EXPERT = "专家"


class ExerciseSet(BaseModel):
    """训练组"""
    set_number: int = Field(default=1)
    reps: int = Field(default=10)
    weight: float = Field(default=0)
    duration: int = Field(default=0)
    rest_time: int = Field(default=60)
    notes: str = Field(default="")


class Exercise(BaseModel):
    """动作"""
    id: str = Field(default="")
    name: str = Field(default="")
    muscle_groups: List[str] = Field(default_factory=list)
    type: str = Field(default="力量训练")
    difficulty: str = Field(default="中等")
    description: str = Field(default="")
    instructions: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    equipment_needed: List[str] = Field(default_factory=list)


class WorkoutSession(BaseModel):
    """训练课程"""
    id: str = Field(default="")
    name: str = Field(default="")
    date: str = Field(default="")
    exercises: List[Dict[str, Any]] = Field(default_factory=list)
    duration_minutes: int = Field(default=60)
    notes: str = Field(default="")
    completed: bool = Field(default=False)


class WorkoutPlan(BaseModel):
    """训练计划"""
    id: str = Field(default="")
    name: str = Field(default="")
    description: str = Field(default="")
    goal: str = Field(default="")
    level: str = Field(default="")
    duration_weeks: int = Field(default=4)
    sessions_per_week: int = Field(default=3)
    sessions: List[WorkoutSession] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_sessions(self) -> int:
        """总训练次数"""
        return self.duration_weeks * self.sessions_per_week
