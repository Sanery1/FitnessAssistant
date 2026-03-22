"""
FastAPI Routes - Body Data
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...tools import registry
from ...memory import MemoryManager
from ...config import settings


router = APIRouter(prefix="/body", tags=["body"])

_memory: Optional[MemoryManager] = None


def get_memory() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager(settings.memory_path)
    return _memory


# 请求模型
class CalculateBMIRequest(BaseModel):
    height: float
    weight: float


class CalculateBodyFatRequest(BaseModel):
    gender: str
    height: float
    waist: float
    neck: float
    hip: Optional[float] = None


class SaveBodyDataRequest(BaseModel):
    user_id: str
    weight: float
    body_fat: Optional[float] = None
    measurements: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class TrackProgressRequest(BaseModel):
    records: List[Dict[str, Any]]


@router.post("/calculate-bmi")
async def calculate_bmi(request: CalculateBMIRequest):
    """计算 BMI"""
    result = registry.execute(
        "calculate_bmi",
        height=request.height,
        weight=request.weight
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/calculate-body-fat")
async def calculate_body_fat(request: CalculateBodyFatRequest):
    """计算体脂率"""
    result = registry.execute(
        "calculate_body_fat",
        gender=request.gender,
        height=request.height,
        waist=request.waist,
        neck=request.neck,
        hip=request.hip
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/track-progress")
async def track_progress(request: TrackProgressRequest):
    """分析进度趋势"""
    result = registry.execute("track_body_progress", records=request.records)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/save")
async def save_body_data(request: SaveBodyDataRequest):
    """保存身体数据"""
    memory = get_memory()

    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "weight": request.weight,
        "body_fat": request.body_fat,
        "measurements": request.measurements,
        "notes": request.notes,
        "saved_at": datetime.now().isoformat()
    }

    memory.save_body_record(request.user_id, data)

    return {"success": True, "message": "身体数据已保存", "data": data}


@router.get("/history/{user_id}")
async def get_body_history(user_id: str, limit: int = 30):
    """获取身体数据历史"""
    memory = get_memory()
    history = memory.get_body_history(user_id, limit)
    return {"user_id": user_id, "history": history}
