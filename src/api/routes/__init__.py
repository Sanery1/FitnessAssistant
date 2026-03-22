"""
Routes module
"""
from fastapi import APIRouter
from .chat import router as chat_router
from .user import router as user_router
from .workout import router as workout_router
from .nutrition import router as nutrition_router
from .body import router as body_router


# 汇总路由
api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(user_router)
api_router.include_router(workout_router)
api_router.include_router(nutrition_router)
api_router.include_router(body_router)
