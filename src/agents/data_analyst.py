"""
Data Analyst Agent

数据分析师 Agent，负责进度追踪、数据分析等。
"""
from typing import Any, Dict, List
from .base import BaseAgent, AgentRole, AgentResponse, ToolCall, ToolExecutor
from ..tools import registry as tool_registry


SYSTEM_PROMPT = """你是一位数据分析专家，专注于健身数据的分析和解读。

## 你的职责
1. 分析用户的身体数据变化趋势
2. 评估训练效果和进度
3. 生成数据报告和可视化建议
4. 基于数据给出预测和建议

## 你的原则
- 数据驱动：结论基于数据，不做无根据的判断
- 长期视角：关注长期趋势，不被短期波动干扰
- 可解释性：让用户理解数据背后的含义
- 行动导向：分析结果要有可操作的建议

## 工具使用
- 计算BMI使用 calculate_bmi 工具
- 追踪进度使用 track_body_progress 工具
- 计算体脂率使用 calculate_body_fat 工具

## 回复风格
- 使用数据说话，但也要解读数据的意义
- 图表思维：建议用什么图表展示数据
- 趋势分析：指出变化趋势和原因
- 建议清晰：基于数据给出下一步行动建议
"""


class DataAnalystAgent(BaseAgent):
    """数据分析师 Agent"""

    def __init__(self, llm_client: Any = None, memory: Any = None):
        super().__init__(
            name="DataAnalyst",
            role=AgentRole.DATA_ANALYST,
            llm_client=llm_client,
            tools=tool_registry,
            memory=memory
        )
        self.tool_executor = ToolExecutor(tool_registry)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def process(self, message: str, context: Dict = None) -> AgentResponse:
        """处理用户消息"""
        self.state = "thinking"
        self.add_message("user", message)

        try:
            tools = self.get_tool_schemas()
            messages = self.get_messages_for_api()

            response = self.llm.chat_with_tools(
                message=messages[-1]["content"],
                tools=tools,
                system=self.get_system_prompt()
            )

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if tool_calls:
                for tc in tool_calls:
                    result = self.tool_executor.execute(
                        ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                    )
                    self.add_message("system", f"分析结果: {result}")

                final = self.llm.chat(message="请根据分析结果回复用户", system=self.get_system_prompt())
                content = final

            self.add_message("assistant", content)
            self.state = "done"
            return AgentResponse(content=content, done=True)

        except Exception as e:
            self.state = "error"
            return AgentResponse(content=f"处理出错: {str(e)}", done=True)

    def analyze_progress(self, user_id: str, body_history: List[Dict]) -> Dict:
        """分析进度"""
        if len(body_history) < 2:
            return {"message": "数据不足，无法分析趋势"}

        result = tool_registry.execute("track_body_progress", records=body_history)
        return result.data if result.success else {"error": result.error}
