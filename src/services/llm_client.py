"""
LLM Client Abstraction Layer

支持多种 LLM 后端:
- GLM (智谱AI) - OpenAI 兼容格式
- OpenAI
- 其他 OpenAI 兼容 API
"""
import os
import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Generator
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(str, Enum):
    """LLM 提供商"""
    GLM = "glm"
    OPENAI = "openai"
    CUSTOM = "custom"


class BaseLLMClient(ABC):
    """LLM 客户端基类"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """对话"""
        pass

    @abstractmethod
    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """带工具的对话"""
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """流式对话"""
        pass


class GLMClient(BaseLLMClient):
    """GLM (智谱AI) 客户端 - OpenAI 兼容格式"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "glm-5"
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://aigw-gzgy2.cucloud.cn:8443/v1")
        self.model = model or os.getenv("LLM_MODEL", "glm-5")

        if not self.api_key:
            raise ValueError("请设置 LLM_API_KEY 环境变量")

        self.client = httpx.Client(timeout=60.0)

    def _build_messages(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None
    ) -> List[Dict]:
        """构建消息列表"""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        result.extend(messages)
        return result

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """对话"""
        full_messages = self._build_messages(messages, system)

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict:
        """带工具的对话"""
        full_messages = self._build_messages(messages, system)

        # 转换 tools 为 OpenAI 格式
        openai_tools = self._convert_tools(tools)

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": full_messages,
                "tools": openai_tools,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]
        result = {
            "content": message.get("content", ""),
            "tool_calls": []
        }

        # 解析工具调用
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                result["tool_calls"].append({
                    "id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "arguments": tool_call["function"]["arguments"]
                })

        return result

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[str, None, None]:
        """流式对话"""
        full_messages = self._build_messages(messages, system)

        with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except Exception:
                        pass

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """转换工具为 OpenAI 格式"""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", tool.get("parameters", {}))
                }
            })
        return openai_tools


class OpenAIClient(BaseLLMClient):
    """OpenAI 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o"
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o")

        if not self.api_key:
            raise ValueError("请设置 LLM_API_KEY 环境变量")

        self.client = httpx.Client(timeout=60.0)

    def _build_messages(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None
    ) -> List[Dict]:
        result = []
        if system:
            result.append({"role": "system", "content": system})
        result.extend(messages)
        return result

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        full_messages = self._build_messages(messages, system)

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict:
        # 实现与 GLMClient 类似
        full_messages = self._build_messages(messages, system)
        openai_tools = [{"type": "function", "function": t} for t in tools]

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": full_messages,
                "tools": openai_tools,
                **kwargs
            }
        )

        response.raise_for_status()
        message = response.json()["choices"][0]["message"]

        return {
            "content": message.get("content", ""),
            "tool_calls": [
                {
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"]
                }
                for tc in message.get("tool_calls", [])
            ]
        }

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        # 实现与 GLMClient 类似
        full_messages = self._build_messages(messages, system)

        with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": full_messages,
                "stream": True,
                **kwargs
            }
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        import json
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except Exception:
                        pass


class LLMClient:
    """统一 LLM 客户端入口"""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GLM,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider

        if provider == LLMProvider.GLM:
            self._client = GLMClient(api_key, base_url, model or "glm-5")
        elif provider == LLMProvider.OPENAI:
            self._client = OpenAIClient(api_key, base_url, model or "gpt-4o")
        else:
            # 自定义使用 OpenAI 兼容格式
            self._client = OpenAIClient(api_key, base_url, model)

        self.conversation_history: List[Dict[str, str]] = []

    def chat(
        self,
        message: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """单轮对话"""
        messages = [{"role": "user", "content": message}]
        return self._client.chat(messages, system, **kwargs)

    def chat_conversation(
        self,
        message: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """多轮对话 (保持历史)"""
        self.conversation_history.append({"role": "user", "content": message})

        response = self._client.chat(self.conversation_history, system, **kwargs)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def chat_with_tools(
        self,
        message: str,
        tools: List[Dict],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """带工具的对话"""
        messages = [{"role": "user", "content": message}]
        return self._client.chat_with_tools(messages, tools, system, **kwargs)

    def stream_chat(
        self,
        message: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """流式对话"""
        messages = [{"role": "user", "content": message}]
        yield from self._client.stream_chat(messages, system, **kwargs)

    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
