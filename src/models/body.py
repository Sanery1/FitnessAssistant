"""
Body data related models
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class BodyComposition(BaseModel):
    """身体成分"""
    body_fat_percent: float = Field(default=0)
    muscle_mass: float = Field(default=0)
    visceral_fat: float = Field(default=0)
    subcutaneous_fat: float = Field(default=0)
    water_percent: float = Field(default=0)
    bone_mass: float = Field(default=0)


class BodyMeasurements(BaseModel):
    """身体围度"""
    chest: float = Field(default=0)
    waist: float = Field(default=0)
    hip: float = Field(default=0)
    bicep_left: float = Field(default=0)
    bicep_right: float = Field(default=0)
    thigh_left: float = Field(default=0)
    thigh_right: float = Field(default=0)
    calf_left: float = Field(default=0)
    calf_right: float = Field(default=0)


class BodyData(BaseModel):
    """身体数据记录"""
    id: str = Field(default="")
    user_id: str = Field(default="")
    date: str = Field(default="")
    weight: float = Field(default=0)
    height: float = Field(default=0)
    composition: Dict[str, float] = Field(default_factory=dict)
    measurements: Dict[str, float] = Field(default_factory=dict)
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def bmi(self) -> float:
        """计算BMI"""
        if self.height > 0:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        return 0
