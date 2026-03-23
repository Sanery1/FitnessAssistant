"""
Tests for Chat Route Session Isolation
"""
import sys
import asyncio
sys.path.insert(0, ".")

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


def run_all_tests():
    print("\n" + "=" * 50)
    print("Chat Route Tests")
    print("=" * 50)

    test_chat_history_isolation()
    print("[PASS] Chat history isolation test passed")

    test_chat_clear_history_scope()
    print("[PASS] Chat clear scope test passed")

    print("\n" + "=" * 50)
    print("All Chat Route Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
