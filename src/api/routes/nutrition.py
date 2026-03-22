"""
FastAPI Routes - Nutrition
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ...tools import registry


router = APIRouter(prefix="/nutrition", tags=["nutrition"])


# 请求模型
class CalculateCaloriesRequest(BaseModel):
    gender: str
    age: int
    height: float
    weight: float
    activity_level: Optional[str] = "中度活动"
    goal: Optional[str] = "保持"


class AnalyzeNutritionRequest(BaseModel):
    foods: List[Dict[str, Any]]
    target_calories: Optional[float] = 2000


@router.post("/calculate-calories")
async def calculate_calories(request: CalculateCaloriesRequest):
    """计算热量需求"""
    result = registry.execute(
        "calculate_calories",
        gender=request.gender,
        age=request.age,
        height=request.height,
        weight=request.weight,
        activity_level=request.activity_level,
        goal=request.goal
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/analyze")
async def analyze_nutrition(request: AnalyzeNutritionRequest):
    """分析营养摄入"""
    result = registry.execute(
        "analyze_nutrition",
        foods=request.foods,
        target_calories=request.target_calories
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.get("/food-database")
async def get_food_database():
    """获取食物数据库 (简化版)"""
    foods = [
        {"name": "米饭", "cal": 116, "protein": 2.6, "carbs": 25.6, "fat": 0.3, "unit": "100g"},
        {"name": "鸡胸肉", "cal": 133, "protein": 23.3, "carbs": 0, "fat": 2.5, "unit": "100g"},
        {"name": "鸡蛋", "cal": 144, "protein": 13.3, "carbs": 1.3, "fat": 9.5, "unit": "100g"},
        {"name": "牛奶", "cal": 54, "protein": 3, "carbs": 4.6, "fat": 3.2, "unit": "100ml"},
        {"name": "西兰花", "cal": 33, "protein": 3.2, "carbs": 4.4, "fat": 0.3, "unit": "100g"},
        {"name": "香蕉", "cal": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "unit": "100g"},
        {"name": "牛肉", "cal": 166, "protein": 20, "carbs": 0, "fat": 9, "unit": "100g"},
        {"name": "三文鱼", "cal": 208, "protein": 20, "carbs": 0, "fat": 13, "unit": "100g"},
    ]
    return {"foods": foods}
