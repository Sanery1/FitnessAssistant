"""
Nutrition related models
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class MealType(str, Enum):
    """餐类型"""
    BREAKFAST = "早餐"
    LUNCH = "午餐"
    DINNER = "晚餐"
    SNACK = "加餐"
    PRE_WORKOUT = "训练前"
    POST_WORKOUT = "训练后"


class FoodItem(BaseModel):
    """食物项"""
    name: str = Field(default="")
    amount: float = Field(default=0)
    unit: str = Field(default="克")
    calories: float = Field(default=0)
    protein: float = Field(default=0)
    carbs: float = Field(default=0)
    fat: float = Field(default=0)
    fiber: float = Field(default=0)


class Meal(BaseModel):
    """餐"""
    type: str = Field(default="早餐")
    time: str = Field(default="")
    foods: List[FoodItem] = Field(default_factory=list)
    notes: str = Field(default="")


class NutritionPlan(BaseModel):
    """营养计划"""
    id: str = Field(default="")
    name: str = Field(default="")
    description: str = Field(default="")
    daily_calories: int = Field(default=2000)
    daily_protein: int = Field(default=150)
    daily_carbs: int = Field(default=200)
    daily_fat: int = Field(default=67)
    meals: List[Meal] = Field(default_factory=list)
    water_intake_liters: float = Field(default=2.5)
    created_at: datetime = Field(default_factory=datetime.now)
