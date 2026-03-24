"""
Tests for Chat Route Session Isolation
"""
import sys
import asyncio
sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from src.main import app
from src.agents.base import AgentResponse
from src.api.routes import chat as chat_route


def reset_chat_globals() -> None:
    """Reset module globals to keep tests isolated."""
    chat_route._memory_managers.clear()
    chat_route._llm_client = None
    chat_route._orchestrators.clear()
    chat_route._knowledge_base = None


def test_chat_history_isolation():
    """Different users should not see the same chat history."""
    reset_chat_globals()

    memory_u1 = chat_route.get_memory("u1")
    memory_u1.add_message("user", "u1-message")
    memory_u1.add_message("assistant", "u1-reply")

    memory_u2 = chat_route.get_memory("u2")
    memory_u2.add_message("user", "u2-message")

    history_u1 = asyncio.run(chat_route.get_history("u1", limit=20))
    history_u2 = asyncio.run(chat_route.get_history("u2", limit=20))

    assert history_u1["messages"] != history_u2["messages"]


def test_chat_clear_history_scope():
    """Clearing one user should not clear all users."""
    reset_chat_globals()

    memory_u1 = chat_route.get_memory("u1")
    memory_u1.add_message("user", "u1-only")

    memory_u2 = chat_route.get_memory("u2")
    memory_u2.add_message("user", "u2-only")

    asyncio.run(chat_route.clear_history("u1"))
    history_u1 = asyncio.run(chat_route.get_history("u1", limit=20))
    history_u2 = asyncio.run(chat_route.get_history("u2", limit=20))

    assert len(history_u1["messages"]) == 0
    assert len(history_u2["messages"]) > 0


def test_chat_message_returns_503_when_agent_failed():
    """Agent 返回处理错误时，接口应返回 503。"""

    class DummyOrchestrator:
        def process(self, _message, _context):
            return AgentResponse(content="处理出错: timeout", done=True)

    reset_chat_globals()

    original = chat_route.get_orchestrator
    chat_route.get_orchestrator = lambda _uid="default": DummyOrchestrator()
    try:
        client = TestClient(app)
        response = client.post(
            "/api/chat/message",
            json={"message": "hello", "user_id": "u_err"},
        )
        assert response.status_code == 503
        assert "LLM" in response.text
    finally:
        chat_route.get_orchestrator = original


def test_chat_message_returns_503_when_error_is_embedded_in_text():
    """多专家拼接文本中包含处理出错时，也应返回 503。"""

    class DummyOrchestrator:
        def process(self, _message, _context):
            return AgentResponse(content="【训练建议】\n处理出错: 429", done=True)

    reset_chat_globals()

    original = chat_route.get_orchestrator
    chat_route.get_orchestrator = lambda _uid="default": DummyOrchestrator()
    try:
        client = TestClient(app)
        response = client.post(
            "/api/chat/message",
            json={"message": "hello", "user_id": "u_err2"},
        )
        assert response.status_code == 503
    finally:
        chat_route.get_orchestrator = original


def run_all_tests():
    print("\n" + "=" * 50)
    print("Chat Route Tests")
    print("=" * 50)

    test_chat_history_isolation()
    print("[PASS] Chat history isolation test passed")

    test_chat_clear_history_scope()
    print("[PASS] Chat clear scope test passed")

    test_chat_message_returns_503_when_agent_failed()
    print("[PASS] Chat message error semantics test passed")

    test_chat_message_returns_503_when_error_is_embedded_in_text()
    print("[PASS] Chat embedded error semantics test passed")

    print("\n" + "=" * 50)
    print("All Chat Route Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
