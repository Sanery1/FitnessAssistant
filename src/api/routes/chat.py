"""
FastAPI Routes - Chat
"""
import asyncio
import time
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
_runtime_llm_config: Dict[str, Optional[str]] = {
    "provider": None,
    "base_url": None,
    "model": None,
    "api_key": None,
}
_runtime_llm_pool: List[Dict[str, Optional[str]]] = []
_active_llm_index: int = 0
_auto_fallback_enabled: bool = True
_fallback_cooldown_seconds: int = 120
_last_failover_at: Optional[float] = None


def get_memory(user_id: str = "default") -> MemoryManager:
    manager = _memory_managers.get(user_id)
    if manager is None:
        manager = MemoryManager(settings.memory_path)
        _memory_managers[user_id] = manager
    return manager


def get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        current = _current_llm_entry()
        provider_text = (current.get("provider") or settings.llm_provider or "glm").lower()
        provider = LLMProvider.GLM if provider_text == "glm" else LLMProvider.OPENAI
        _llm_client = LLMClient(
            provider=provider,
            api_key=current.get("api_key") or settings.llm_api_key,
            base_url=current.get("base_url") or settings.llm_base_url,
            model=current.get("model") or settings.llm_model,
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


class LLMConfigRequest(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class LLMConfigResponse(BaseModel):
    provider: str
    base_url: str
    model: str
    has_api_key: bool


class LLMPoolItem(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key: Optional[str] = None


class LLMPoolRequest(BaseModel):
    configs: List[LLMPoolItem]
    active_index: int = 0
    auto_fallback_enabled: bool = True
    fallback_cooldown_seconds: int = 120


class LLMPoolItemView(BaseModel):
    provider: str
    base_url: str
    model: str
    has_api_key: bool


class LLMPoolResponse(BaseModel):
    active_index: int
    configs: List[LLMPoolItemView]
    auto_fallback_enabled: bool
    fallback_cooldown_seconds: int
    seconds_since_failover: Optional[int]


def _friendly_llm_error(detail: str) -> str:
    """Map low-level provider errors to user-friendly messages."""
    text = (detail or "").lower()
    if "429" in text or "too many requests" in text:
        return "LLM 服务繁忙（请求过多），请稍后重试。"
    if "timed out" in text or "timeout" in text:
        return "LLM 服务响应超时，请稍后重试。"
    if "api_key" in text or "unauthorized" in text or "401" in text:
        return "LLM 服务鉴权失败，请检查 API Key 配置。"
    return "LLM 服务暂时不可用，请稍后重试。"


def _is_quota_or_rate_limit_error(detail: str) -> bool:
    text = (detail or "").lower()
    markers = [
        "429",
        "too many requests",
        "rate limit",
        "quota",
        "insufficient_quota",
    ]
    return any(marker in text for marker in markers)


def _contains_agent_failure(content: str) -> bool:
    text = (content or "").lower()
    markers = [
        "处理出错:",
        "too many requests",
        "timed out",
        "timeout",
        "client error",
        "server error",
        "httpstatuserror",
        "429",
    ]
    return any(marker in text for marker in markers)


def _current_llm_entry() -> Dict[str, Optional[str]]:
    if _runtime_llm_pool:
        index = min(max(_active_llm_index, 0), len(_runtime_llm_pool) - 1)
        return _runtime_llm_pool[index]
    return _runtime_llm_config


def _switch_to_next_llm() -> bool:
    """切换到下一个 LLM 配置。返回是否切换成功。"""
    global _active_llm_index, _llm_client, _last_failover_at

    if len(_runtime_llm_pool) <= 1:
        return False

    next_index = _active_llm_index + 1
    if next_index >= len(_runtime_llm_pool):
        return False

    _active_llm_index = next_index
    _last_failover_at = time.time()
    _llm_client = None
    _orchestrators.clear()
    return True


def _maybe_switch_back_to_primary() -> bool:
    """当主模型可能恢复时自动回切。"""
    global _active_llm_index, _llm_client

    if not _auto_fallback_enabled:
        return False

    if len(_runtime_llm_pool) <= 1 or _active_llm_index == 0:
        return False

    if _last_failover_at is None:
        return False

    elapsed = time.time() - _last_failover_at
    if elapsed < _fallback_cooldown_seconds:
        return False

    _active_llm_index = 0
    _llm_client = None
    _orchestrators.clear()
    return True


def _current_llm_config() -> LLMConfigResponse:
    current = _current_llm_entry()
    provider = (current.get("provider") or settings.llm_provider or "glm").lower()
    base_url = current.get("base_url") or settings.llm_base_url
    model = current.get("model") or settings.llm_model
    api_key = current.get("api_key") or settings.llm_api_key
    return LLMConfigResponse(
        provider=provider,
        base_url=base_url,
        model=model,
        has_api_key=bool(api_key),
    )


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """发送消息并获取回复"""
    try:
        _maybe_switch_back_to_primary()

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

        # Agent 内部失败时，避免返回 200 + 错误文本造成调用方误判。
        # 注意：多专家拼接回复可能是“【训练建议】...处理出错: ...”。
        if isinstance(response.content, str) and _contains_agent_failure(response.content):
            # 当前 LLM 限额/频控时，自动切换到下一个并重试一次
            if _is_quota_or_rate_limit_error(response.content) and _switch_to_next_llm():
                orchestrator = get_orchestrator(user_id)
                response = await asyncio.to_thread(
                    orchestrator.process,
                    request.message,
                    user_context,
                )

            if isinstance(response.content, str) and _contains_agent_failure(response.content):
                raise HTTPException(status_code=503, detail=_friendly_llm_error(response.content))

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
    _maybe_switch_back_to_primary()

    llm = get_llm()
    knowledge = get_knowledge()

    # 获取相关知识
    context = knowledge.get_context(request.message)

    async def generate():
        try:
            system_prompt = f"你是一个专业的健身助手。{context}"
            for chunk in llm.stream_chat(request.message, system=system_prompt):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            # 流式接口也支持限额自动切换并重试一次
            if _is_quota_or_rate_limit_error(str(exc)) and _switch_to_next_llm():
                try:
                    llm2 = get_llm()
                    system_prompt = f"你是一个专业的健身助手。{context}"
                    for chunk in llm2.stream_chat(request.message, system=system_prompt):
                        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                except Exception as exc2:
                    fallback = _friendly_llm_error(str(exc2))
                    yield f"data: {json.dumps({'content': fallback}, ensure_ascii=False)}\n\n"
            else:
                fallback = _friendly_llm_error(str(exc))
                yield f"data: {json.dumps({'content': fallback}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/llm-config", response_model=LLMConfigResponse)
async def get_llm_config():
    """获取当前对话使用的 LLM 配置（不返回明文 API Key）。"""
    return _current_llm_config()


@router.put("/llm-config", response_model=LLMConfigResponse)
async def update_llm_config(request: LLMConfigRequest):
    """更新对话 LLM 运行时配置，更新后立即生效。"""
    global _llm_client, _active_llm_index

    if request.provider is not None:
        provider = request.provider.strip().lower()
        if provider not in {"glm", "openai"}:
            raise HTTPException(status_code=400, detail="provider 仅支持 glm 或 openai")
        _runtime_llm_config["provider"] = provider

    if request.base_url is not None:
        _runtime_llm_config["base_url"] = request.base_url.strip() or None

    if request.model is not None:
        _runtime_llm_config["model"] = request.model.strip() or None

    if request.api_key is not None:
        _runtime_llm_config["api_key"] = request.api_key.strip() or None

    # 单配置模式下清空池并重置 active index
    _runtime_llm_pool.clear()
    _active_llm_index = 0

    # 清空客户端和编排器实例，让新配置立即生效
    _llm_client = None
    _orchestrators.clear()

    return _current_llm_config()


@router.get("/llm-pool", response_model=LLMPoolResponse)
async def get_llm_pool():
    """获取当前 LLM 池配置（不返回明文 API Key）。"""
    if _runtime_llm_pool:
        configs = _runtime_llm_pool
        active = min(max(_active_llm_index, 0), len(configs) - 1)
    else:
        current = _current_llm_entry()
        configs = [current]
        active = 0

    seconds_since_failover = None
    if _last_failover_at is not None:
        seconds_since_failover = int(max(0, time.time() - _last_failover_at))

    return LLMPoolResponse(
        active_index=active,
        configs=[
            LLMPoolItemView(
                provider=(item.get("provider") or settings.llm_provider or "glm").lower(),
                base_url=item.get("base_url") or settings.llm_base_url,
                model=item.get("model") or settings.llm_model,
                has_api_key=bool(item.get("api_key") or settings.llm_api_key),
            )
            for item in configs
        ],
        auto_fallback_enabled=_auto_fallback_enabled,
        fallback_cooldown_seconds=_fallback_cooldown_seconds,
        seconds_since_failover=seconds_since_failover,
    )


@router.put("/llm-pool", response_model=LLMPoolResponse)
async def update_llm_pool(request: LLMPoolRequest):
    """更新 LLM 池，支持限额自动切换。"""
    global _llm_client, _active_llm_index, _auto_fallback_enabled, _fallback_cooldown_seconds

    if not request.configs:
        raise HTTPException(status_code=400, detail="configs 不能为空")

    normalized: List[Dict[str, Optional[str]]] = []
    for item in request.configs:
        provider = item.provider.strip().lower()
        if provider not in {"glm", "openai"}:
            raise HTTPException(status_code=400, detail="provider 仅支持 glm 或 openai")

        normalized.append(
            {
                "provider": provider,
                "base_url": item.base_url.strip() or None,
                "model": item.model.strip() or None,
                "api_key": (item.api_key or "").strip() or None,
            }
        )

    if request.active_index < 0 or request.active_index >= len(normalized):
        raise HTTPException(status_code=400, detail="active_index 超出范围")

    _runtime_llm_pool.clear()
    _runtime_llm_pool.extend(normalized)
    _active_llm_index = request.active_index
    _auto_fallback_enabled = request.auto_fallback_enabled
    _fallback_cooldown_seconds = max(5, int(request.fallback_cooldown_seconds))

    # 为避免单配置与池配置冲突，重置单配置覆盖
    _runtime_llm_config["provider"] = None
    _runtime_llm_config["base_url"] = None
    _runtime_llm_config["model"] = None
    _runtime_llm_config["api_key"] = None

    _llm_client = None
    _orchestrators.clear()

    return await get_llm_pool()


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
