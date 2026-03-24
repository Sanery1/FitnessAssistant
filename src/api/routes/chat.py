"""
FastAPI Routes - Chat
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

from ...services import LLMClient, LLMProvider
from ...agents import OrchestratorAgent
from ...memory import MemoryManager
from ...knowledge import KnowledgeBase
from ...config import settings


router = APIRouter(prefix="/chat", tags=["chat"])

# 全局实例 (生产环境应使用依赖注入)
_memory_managers: Dict[str, MemoryManager] = {}
_llm_client: Optional[LLMClient] = None
_orchestrators: Dict[str, OrchestratorAgent] = {}
_knowledge_base: Optional[KnowledgeBase] = None


def get_memory(user_id: str = "default") -> MemoryManager:
    manager = _memory_managers.get(user_id)
    if manager is None:
        manager = MemoryManager(settings.memory_path)
        _memory_managers[user_id] = manager
    return manager


def get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        provider = LLMProvider.GLM if settings.llm_provider == "glm" else LLMProvider.OPENAI
        _llm_client = LLMClient(
            provider=provider,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model
        )
    return _llm_client


def get_knowledge() -> KnowledgeBase:
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase(settings.knowledge_path)
        from ...knowledge import init_fitness_knowledge
        init_fitness_knowledge(_knowledge_base)
    return _knowledge_base


def get_orchestrator(user_id: str = "default") -> OrchestratorAgent:
    orchestrator = _orchestrators.get(user_id)
    if orchestrator is None:
        orchestrator = OrchestratorAgent(
            llm_client=get_llm(),
            memory=get_memory(user_id)
        )
        _orchestrators[user_id] = orchestrator
    return orchestrator


# 请求模型
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    content: str
    user_id: str
    done: bool = True


class StreamRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """发送消息并获取回复"""
    try:
        user_id = request.user_id or "default"
        orchestrator = get_orchestrator(user_id)
        memory = get_memory(user_id)

        # 获取用户上下文
        user_context = memory.get_user_context(user_id)

        # 处理消息
        response = await asyncio.to_thread(
            orchestrator.process,
            request.message,
            user_context
        )

        # Agent 内部失败时，避免返回 200 + 错误文本造成调用方误判
        if isinstance(response.content, str) and response.content.startswith("处理出错:"):
            raise HTTPException(status_code=503, detail=response.content)

        # 保存对话
        memory.add_message("user", request.message)
        memory.add_message("assistant", response.content)

        return ChatResponse(
            content=response.content,
            user_id=user_id,
            done=response.done
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: StreamRequest):
    """流式对话"""
    llm = get_llm()
    knowledge = get_knowledge()

    # 获取相关知识
    context = knowledge.get_context(request.message)

    async def generate():
        system_prompt = f"你是一个专业的健身助手。{context}"
        for chunk in llm.stream_chat(request.message, system=system_prompt):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    """获取对话历史"""
    memory = get_memory(user_id)
    messages = memory.get_conversation(limit)
    return {"user_id": user_id, "messages": messages}


@router.delete("/history/{user_id}")
async def clear_history(user_id: str):
    """清空对话历史"""
    memory = get_memory(user_id)
    memory.clear_session()
    return {"success": True, "message": "对话历史已清空"}


@router.get("/tools")
async def list_tools():
    """列出可用工具"""
    from ...tools import registry
    tools = registry.list_tools()
    return {"tools": tools}
