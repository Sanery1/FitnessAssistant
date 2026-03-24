"""
Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # App
    app_name: str = "Fitness AI Assistant"
    debug: bool = False
    version: str = "0.1.0"

    # LLM
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    llm_model: str = "glm-4-plus"
    llm_provider: str = "glm"
    llm_fallback_models: str = ""

    # OpenAI-compatible aliases (optional)
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    https_proxy: Optional[str] = None
    http_proxy: Optional[str] = None

    # Storage
    data_path: str = "data"
    memory_path: str = "data/memory"
    knowledge_path: str = "data/knowledge"

    # API
    api_prefix: str = "/api"
    cors_allow_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "*"

    @property
    def cors_origins(self) -> List[str]:
        return [item.strip() for item in self.cors_allow_origins.split(",") if item.strip()]

    @property
    def cors_methods(self) -> List[str]:
        return [item.strip().upper() for item in self.cors_allow_methods.split(",") if item.strip()]

    @property
    def cors_headers(self) -> List[str]:
        return [item.strip() for item in self.cors_allow_headers.split(",") if item.strip()]

    @property
    def effective_llm_api_key(self) -> Optional[str]:
        return self.llm_api_key or self.openai_api_key

    @property
    def effective_llm_base_url(self) -> str:
        return self.llm_base_url or self.openai_base_url or "https://open.bigmodel.cn/api/paas/v4"

    @property
    def llm_pool_models(self) -> List[str]:
        return [item.strip() for item in self.llm_fallback_models.split(",") if item.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 映射环境变量名
        env_prefix = ""


# 统一从 BaseSettings + .env 读取配置
settings = Settings()
