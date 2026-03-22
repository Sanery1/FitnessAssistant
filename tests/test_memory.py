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
    print("\n📝 短期记忆测试")

    memory = ShortTermMemory()

    # 添加消息
    memory.add_message("user", "你好")
    memory.add_message("assistant", "你好！我是健身助手")

    assert memory.message_count == 2
    assert memory.has_messages

    # 获取上下文
    messages = memory.get_messages()
    assert len(messages) == 2

    # 搜索
    results = memory.search("健身")
    assert len(results) == 1

    print("✅ 短期记忆测试通过")


def test_long_term_memory():
    """测试长期记忆"""
    print("\n💾 长期记忆测试")

    memory = LongTermMemory("data/memory/test")

    # 保存用户数据
    memory.save_user_profile("test_user", {
        "name": "测试用户",
        "age": 25,
        "fitness_level": "初学者"
    })

    # 读取
    profile = memory.get_user_profile("test_user")
    assert profile is not None
    assert profile["name"] == "测试用户"

    # 保存训练记录
    memory.save_workout_history("test_user", {
        "date": "2026-03-19",
        "type": "力量训练",
        "duration": 60
    })

    history = memory.get_workout_history("test_user")
    assert len(history) == 1

    print("✅ 长期记忆测试通过")


def test_memory_manager():
    """测试 Memory 管理器"""
    print("\n🗂️ Memory 管理器测试")

    manager = MemoryManager("data/memory/test")

    # 添加对话
    manager.add_message("user", "帮我制定训练计划")
    manager.add_message("assistant", "好的，请告诉我你的目标")

    conversation = manager.get_conversation()
    assert len(conversation) == 2

    # 保存用户
    manager.save_user("test_user_2", {
        "name": "测试用户2",
        "goals": ["减脂"]
    })

    # 获取上下文
    context = manager.get_user_context("test_user_2")
    assert "user_profile" in context

    # 统计
    stats = manager.get_stats()
    print(f"   消息数: {stats['short_term']['message_count']}")

    print("✅ Memory 管理器测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("🧪 Memory 系统测试")
    print("=" * 50)

    test_short_term_memory()
    test_long_term_memory()
    test_memory_manager()

    print("\n" + "=" * 50)
    print("✅ 所有 Memory 测试通过!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
