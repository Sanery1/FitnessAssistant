"""
Run All Tests
"""
import sys
sys.path.insert(0, ".")

from test_tools import run_all_tests as run_tool_tests
from test_memory import run_all_tests as run_memory_tests
from test_workflow import run_all_tests as run_workflow_tests


def main():
    print("\n" + "=" * 60)
    print("🚀 健身 AI 助手 - 测试套件")
    print("=" * 60)

    # 工具测试
    run_tool_tests()

    # Memory 测试
    run_memory_tests()

    # 工作流测试
    run_workflow_tests()

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！项目构建成功！")
    print("=" * 60)

    print("""
📋 使用说明:

1. 配置 API 密钥
   cp .env.example .env
   # 编辑 .env 填入你的 GLM API Key

2. 安装依赖
   pip install -r requirements.txt

3. 启动服务
   python -m src.main --reload

4. 访问界面
   打开 http://localhost:8000

5. API 文档
   打开 http://localhost:8000/docs
    """)


if __name__ == "__main__":
    main()
