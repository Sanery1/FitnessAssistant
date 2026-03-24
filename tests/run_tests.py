"""
Run All Tests
"""
import sys

sys.path.insert(0, ".")

from test_tools import run_all_tests as run_tool_tests
from test_llm_client import run_all_tests as run_llm_tests
from test_memory import run_all_tests as run_memory_tests
from test_workflow import run_all_tests as run_workflow_tests
from test_chat import run_all_tests as run_chat_tests
from test_api_integration import run_all_tests as run_api_integration_tests
from test_api_edge_cases import run_all_tests as run_api_edge_case_tests
from test_performance_baseline import run_all_tests as run_performance_tests


def main():
    print("\n" + "=" * 60)
    print("Fitness AI Assistant - Test Suite")
    print("=" * 60)

    # 工具测试
    run_tool_tests()

    # LLM 客户端工具函数测试
    run_llm_tests()

    # Memory 测试
    run_memory_tests()

    # 工作流测试
    run_workflow_tests()

    # 聊天路由测试
    run_chat_tests()

    # API 集成测试
    run_api_integration_tests()

    # API 异常路径测试
    run_api_edge_case_tests()

    # 性能基线测试
    run_performance_tests()

    print("\n" + "=" * 60)
    print("All Tests Passed! Project Build Successful!")
    print("=" * 60)

    print(
        """
Usage:

1. Configure API Key
   cp .env.example .env
   # Edit .env and fill in your GLM API Key

2. Install Dependencies
   pip install -r requirements.txt

3. Start Service
   python -m src.main --reload

4. Access Web Interface
   Open http://localhost:8000

5. API Documentation
   Open http://localhost:8000/docs
    """
    )


if __name__ == "__main__":
    main()
