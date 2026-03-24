"""
LLM Client Abstraction Layer

支持多种 LLM 后端:
- GLM (智谱AI) - OpenAI 兼容格式
- OpenAI
- 其他 OpenAI 兼容 API
"""
import asyncio
import json
import os
import re
import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Generator
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


def normalize_tool_arguments(arguments: Any) -> Dict[str, Any]:
    """Normalize tool-call arguments into a dictionary."""
    if isinstance(arguments, dict):
        return arguments

    if isinstance(arguments, str):
        text = arguments.strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"工具参数 JSON 解析失败: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("工具参数必须是 JSON 对象")
        return data

    raise ValueError("工具参数类型无效，必须为 dict 或 JSON 字符串")


def _coerce_parameter_value(raw: str) -> Any:
    text = (raw or "").strip()
    if not text:
        return ""
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except Exception:
            return text
    if re.fullmatch(r"-?\d+\.\d+", text):
        try:
            return float(text)
        except Exception:
            return text
    return text


def extract_compat_tool_calls(content: str) -> Dict[str, Any]:
    """Extract tool calls from compatibility text formats (e.g. minimax XML-like tags)."""
    original = content or ""
    blocks = re.findall(r"<invoke\s+name=\"([^\"]+)\">(.*?)</invoke>", original, flags=re.DOTALL)
    tool_calls: List[Dict[str, Any]] = []

    for idx, (name, body) in enumerate(blocks):
        params: Dict[str, Any] = {}
        pairs = re.findall(r"<parameter\s+name=\"([^\"]+)\">(.*?)</parameter>", body, flags=re.DOTALL)
        for key, value in pairs:
            params[key] = _coerce_parameter_value(value)

        tool_calls.append(
            {
                "id": f"compat_call_{idx + 1}",
                "name": name.strip(),
                "arguments": params,
            }
        )

    if not tool_calls:
        tool_code_blocks = re.findall(
            r"<tool_code>\s*\{(.*?)\}\s*</tool_code>",
            original,
            flags=re.DOTALL,
        )
        for idx, block in enumerate(tool_code_blocks):
            name_match = re.search(r"tool\s*=>\s*'([^']+)'", block)
            args_match = re.search(r"args\s*=>\s*'(.*?)'", block, flags=re.DOTALL)
            if not name_match:
                continue

            args_text = args_match.group(1) if args_match else ""
            args_text = args_text.replace("\\n", "\n")
            params: Dict[str, Any] = {}
            for key, value in re.findall(r"<([a-zA-Z_][a-zA-Z0-9_]*)>(.*?)</\1>", args_text, flags=re.DOTALL):
                params[key] = _coerce_parameter_value(value)

            tool_calls.append(
                {
                    "id": f"compat_tool_code_{idx + 1}",
                    "name": name_match.group(1).strip(),
                    "arguments": params,
                }
            )

    if not tool_calls:
        tool_blocks = re.findall(
            r"<tool\s+name=\"([^\"]+)\">(.*?)</tool>",
            original,
            flags=re.DOTALL,
        )
        for idx, (name, body) in enumerate(tool_blocks):
            params: Dict[str, Any] = {}
            for key, value in re.findall(r"<param\s+name=\"([^\"]+)\">(.*?)</param>", body, flags=re.DOTALL):
                params[key] = _coerce_parameter_value(value)
            tool_calls.append(
                {
                    "id": f"compat_tool_block_{idx + 1}",
                    "name": name.strip(),
                    "arguments": params,
                }
            )

    if not tool_calls:
        function_call_blocks = re.findall(
            r"<FunctionCall>(.*?)</FunctionCall>",
            original,
            flags=re.DOTALL | re.IGNORECASE,
        )
        for idx, block in enumerate(function_call_blocks):
            name_match = re.search(r"tool\s*:\s*\"([^\"]+)\"", block)
            if not name_match:
                continue

            params: Dict[str, Any] = {}
            args_match = re.search(r"args\s*:\s*\{(.*?)\}", block, flags=re.DOTALL)
            if args_match:
                args_body = args_match.group(1)
                for key, value in re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|:)\s*([^\n,}]+)", args_body):
                    params[key] = _coerce_parameter_value(value.strip().strip('"').strip("'"))

            tool_calls.append(
                {
                    "id": f"compat_function_call_{idx + 1}",
                    "name": name_match.group(1).strip(),
                    "arguments": params,
                }
            )

    # Remove wrapper tags to avoid leaking raw tool markup to UI.
    cleaned = re.sub(r"<minimax:tool_call>.*?</minimax:tool_call>", "", original, flags=re.DOTALL)
    cleaned = re.sub(r"<tool_code>.*?</tool_code>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<tool_call>.*?</tool_call>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<FunctionCall>.*?</FunctionCall>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<invoke\s+name=\"[^\"]+\">.*?</invoke>", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    return {
        "content": cleaned,
        "tool_calls": tool_calls,
    }


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
                    "arguments": normalize_tool_arguments(tool_call["function"].get("arguments", {}))
                })

        if not result["tool_calls"] and result["content"]:
            compat = extract_compat_tool_calls(result["content"])
            if compat["tool_calls"]:
                result["tool_calls"] = compat["tool_calls"]
                result["content"] = compat["content"]

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

        result = {
            "content": message.get("content", ""),
            "tool_calls": [
                {
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": normalize_tool_arguments(tc["function"].get("arguments", {}))
                }
                for tc in message.get("tool_calls", [])
            ]
        }

        if not result["tool_calls"] and result["content"]:
            compat = extract_compat_tool_calls(result["content"])
            if compat["tool_calls"]:
                result["tool_calls"] = compat["tool_calls"]
                result["content"] = compat["content"]

        return result

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

    async def achat(
        self,
        message: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """异步单轮对话（线程封装）。"""
        return await asyncio.to_thread(self.chat, message, system, **kwargs)

    async def achat_with_tools(
        self,
        message: str,
        tools: List[Dict],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """异步工具对话（线程封装）。"""
        return await asyncio.to_thread(self.chat_with_tools, message, tools, system, **kwargs)

    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
