"""
FastAPI Routes - User
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...memory import MemoryManager
from ...models import UserProfile, User
from ...config import settings


router = APIRouter(prefix="/user", tags=["user"])

_memory: Optional[MemoryManager] = None


def get_memory() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager(settings.memory_path)
    return _memory


# 请求模型
class CreateUserRequest(BaseModel):
    name: str
    profile: Dict[str, Any]


class UpdateProfileRequest(BaseModel):
    profile: Dict[str, Any]


@router.post("/create")
async def create_user(request: CreateUserRequest):
    """创建用户"""
    memory = get_memory()
    user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    user_data = {
        "id": user_id,
        "name": request.name,
        "profile": request.profile,
        "created_at": datetime.now().isoformat()
    }

    memory.save_user(user_id, user_data)

    return {"success": True, "user_id": user_id, "user": user_data}


@router.get("/{user_id}")
async def get_user(user_id: str):
    """获取用户信息"""
    memory = get_memory()
    user = memory.get_user(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


@router.put("/{user_id}/profile")
async def update_profile(user_id: str, request: UpdateProfileRequest):
    """更新用户档案"""
    memory = get_memory()
    user = memory.get_user(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    user["profile"].update(request.profile)
    user["updated_at"] = datetime.now().isoformat()

    memory.save_user(user_id, user)

    return {"success": True, "user": user}


@router.get("/{user_id}/context")
async def get_user_context(user_id: str):
    """获取用户完整上下文"""
    memory = get_memory()
    context = memory.get_user_context(user_id)
    return context
