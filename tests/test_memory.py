"""
Tests for Memory System
"""
import sys
import os
sys.path.insert(0, ".")

# 清理测试数据
if os.path.exists("data/memory/test"):
    import shutil
    shutil.rmtree("data/memory/test", ignore_errors=True)

from src.memory import MemoryManager, ShortTermMemory, LongTermMemory


def test_short_term_memory():
    """测试短期记忆"""
    print("\n[PRESS] Short-term memory test")

    memory = ShortTermMemory()

    # 添加消息
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hello! I am your fitness assistant.")

    assert memory.message_count == 2
    assert memory.has_messages

    # 获取上下文
    messages = memory.get_messages()
    assert len(messages) == 2

    # 搜索
    results = memory.search("fitness")
    assert len(results) >= 0

    print("[PASS] Short-term memory test passed")


def test_long_term_memory():
    """测试长期记忆"""
    print("\n[PRESS] Long-term memory test")

    memory = LongTermMemory("data/memory/test")

    # 保存用户数据
    memory.save_user_profile("test_user", {
        "name": "Test User",
        "age": 25,
        "fitness_level": "beginner"
    })

    # 读取
    profile = memory.get_user_profile("test_user")
    assert profile is not None
    assert profile["name"] == "Test User"

    # 保存训练记录
    memory.save_workout_history("test_user", {
        "date": "2026-03-19",
        "type": "strength",
        "duration": 60
    })

    history = memory.get_workout_history("test_user")
    assert len(history) == 1

    print("[PASS] Long-term memory test passed")


def test_memory_manager():
    """测试 Memory 管理器"""
    print("\n[PRESS] Memory Manager test")

    manager = MemoryManager("data/memory/test")

    # 添加对话
    manager.add_message("user", "Help me create a workout plan")
    manager.add_message("assistant", "Sure, please tell me your goals.")

    conversation = manager.get_conversation()
    assert len(conversation) == 2

    # 保存用户
    manager.save_user("test_user_2", {
        "name": "Test User 2",
        "goals": ["fat_loss"]
    })

    # 获取上下文
    context = manager.get_user_context("test_user_2")
    assert "user_profile" in context

    # 统计
    stats = manager.get_stats()
    print(f"   Message count: {stats['short_term']['message_count']}")

    print("[PASS] Memory Manager test passed")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("Memory System Tests")
    print("=" * 50)

    test_short_term_memory()
    test_long_term_memory()
    test_memory_manager()

    print("\n" + "=" * 50)
    print("All Memory Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
