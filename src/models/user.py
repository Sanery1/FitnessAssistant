"""
User related models
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class FitnessGoal(str, Enum):
    """健身目标"""
    LOSE_WEIGHT = "减脂"
    GAIN_MUSCLE = "增肌"
    MAINTAIN = "保持"
    IMPROVE_ENDURANCE = "提升耐力"
    IMPROVE_STRENGTH = "提升力量"
    GENERAL_FITNESS = "综合健身"


class FitnessLevel(str, Enum):
    """健身水平"""
    BEGINNER = "初学者"
    INTERMEDIATE = "中级"
    ADVANCED = "高级"
    EXPERT = "专家"


class Gender(str, Enum):
    """性别"""
    MALE = "男"
    FEMALE = "女"
    OTHER = "其他"


class UserProfile(BaseModel):
    """用户档案"""
    gender: str = Field(default="男")
    age: int = Field(default=25)
    height: float = Field(default=170)
    weight: float = Field(default=70)
    fitness_level: str = Field(default="初学者")
    fitness_goals: List[str] = Field(default_factory=list)
    training_days_per_week: int = Field(default=3)
    available_time_per_day: int = Field(default=60)
    injuries: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)

    @property
    def bmi(self) -> float:
        """计算BMI"""
        height_m = self.height / 100
        return round(self.weight / (height_m ** 2), 2)

    @property
    def bmi_category(self) -> str:
        """BMI分类"""
        bmi = self.bmi
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            return "正常"
        elif bmi < 28:
            return "偏胖"
        else:
            return "肥胖"


class User(BaseModel):
    """用户模型"""
    id: str = Field(default="")
    name: str = Field(default="")
    profile: UserProfile = Field(default_factory=UserProfile)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
