"""
Fitness AI Assistant - Main Entry

Usage:
    python -m src.main --help
    uvicorn src.main:app --reload
"""
import argparse
import uvicorn
from pathlib import Path

from .config import settings


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description=settings.app_name)
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    parser.add_argument('--reload', action='store_true', help='开发模式热重载')
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════╗
║     💪 {settings.app_name} v{settings.version}     ║
╠══════════════════════════════════════════╣
║  LLM Provider: {settings.llm_provider:<20}      ║
║  LLM Model:    {settings.llm_model:<20}      ║
╚══════════════════════════════════════════╝
    """)

    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
