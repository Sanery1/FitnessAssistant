"""
Progress tracking models
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class ProgressSnapshot(BaseModel):
    """进度快照"""
    date: str = Field(default="")
    weight: float = Field(default=0)
    body_fat_percent: float = Field(default=0)
    workout_count: int = Field(default=0)
    total_workout_minutes: int = Field(default=0)
    calories_burned: int = Field(default=0)


class ProgressRecord(BaseModel):
    """进度记录"""
    id: str = Field(default="")
    user_id: str = Field(default="")
    snapshots: List[ProgressSnapshot] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    def add_snapshot(self, snapshot: ProgressSnapshot) -> None:
        """添加快照"""
        self.snapshots.append(snapshot)

    def get_latest(self) -> Optional[ProgressSnapshot]:
        """获取最新快照"""
        return self.snapshots[-1] if self.snapshots else None

    @property
    def total_workouts(self) -> int:
        """总训练次数"""
        return sum(s.workout_count for s in self.snapshots)

    @property
    def total_minutes(self) -> int:
        """总训练时长"""
        return sum(s.total_workout_minutes for s in self.snapshots)
