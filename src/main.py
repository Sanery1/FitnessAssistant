"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .config import settings
from .api.routes import api_router


# 创建应用
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# 注册 API 路由
app.include_router(api_router, prefix=settings.api_prefix)


# 静态文件服务
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """主页"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": f"Welcome to {settings.app_name}", "docs": "/docs"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "version": settings.version}


# 启动事件
@app.on_event("startup")
async def startup():
    """启动时初始化"""
    from .knowledge import KnowledgeBase, init_fitness_knowledge

    # 初始化知识库
    kb = KnowledgeBase(settings.knowledge_path)
    init_fitness_knowledge(kb)

    print(f"[OK] {settings.app_name} v{settings.version} started!")
    print(f"[API] Docs: http://localhost:8000/docs")
