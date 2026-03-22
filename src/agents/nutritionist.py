"""
Nutritionist Agent

营养师 Agent，负责营养计算、饮食建议等。
"""
from typing import Any, Dict, List
from .base import BaseAgent, AgentRole, AgentResponse, ToolCall, ToolExecutor
from ..tools import registry as tool_registry


SYSTEM_PROMPT = """你是一位专业的营养师，擅长运动营养和健康饮食规划。

## 你的职责
1. 根据用户目标计算热量和营养需求
2. 提供个性化的饮食建议
3. 分析用户的饮食记录，给出改进建议
4. 解答营养相关问题

## 你的原则
- 科学性：基于营养学原理，不传播伪科学
- 可持续性：推荐可持续的饮食方案，而非极端节食
- 个性化：考虑用户的生活习惯和偏好
- 均衡性：强调营养均衡，不偏废任何营养素

## 工具使用
- 计算热量需求使用 calculate_calories 工具
- 分析饮食记录使用 analyze_nutrition 工具

## 回复风格
- 数据清晰，使用具体数字
- 给出可操作的建议
- 解释原因，让用户理解"为什么"
- 关联运动目标，说明营养与训练的关系
"""


class NutritionistAgent(BaseAgent):
    """营养师 Agent"""

    def __init__(self, llm_client: Any = None, memory: Any = None):
        super().__init__(
            name="Nutritionist",
            role=AgentRole.NUTRITIONIST,
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
                    self.add_message("system", f"工具执行结果: {result}")

                final = self.llm.chat(message="请根据工具结果回复用户", system=self.get_system_prompt())
                content = final

            self.add_message("assistant", content)
            self.state = "done"
            return AgentResponse(content=content, done=True)

        except Exception as e:
            self.state = "error"
            return AgentResponse(content=f"处理出错: {str(e)}", done=True)

    def calculate_nutrition_needs(
        self,
        gender: str,
        age: int,
        height: float,
        weight: float,
        activity_level: str,
        goal: str
    ) -> Dict:
        """计算营养需求"""
        result = tool_registry.execute(
            "calculate_calories",
            gender=gender,
            age=age,
            height=height,
            weight=weight,
            activity_level=activity_level,
            goal=goal
        )
        return result.data if result.success else {"error": result.error}
