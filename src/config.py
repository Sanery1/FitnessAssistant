"""
Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # App
    app_name: str = "Fitness AI Assistant"
    debug: bool = True
    version: str = "0.1.0"

    # LLM
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://aigw-gzgy2.cucloud.cn:8443/v1"
    llm_model: str = "glm-5"
    llm_provider: str = "glm"

    # Storage
    data_path: str = "data"
    memory_path: str = "data/memory"
    knowledge_path: str = "data/knowledge"

    # API
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 映射环境变量名
        env_prefix = ""


# 从环境变量获取配置
settings = Settings(
    llm_api_key=os.getenv("LLM_API_KEY"),
    llm_base_url=os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
    llm_model=os.getenv("LLM_MODEL", "glm-4-plus"),
    llm_provider=os.getenv("LLM_PROVIDER", "glm"),
)
