"""
Fitness Coach Agent

健身教练 Agent，负责训练计划生成、动作指导等。
"""
from typing import Any, Dict, List, Optional
from .base import BaseAgent, AgentRole, AgentResponse, ToolCall, ToolExecutor
from ..tools import registry as tool_registry


SYSTEM_PROMPT = """你是一位专业的健身教练，拥有丰富的健身知识和教学经验。

## 你的职责
1. 根据用户的目标、水平和条件，设计个性化的训练计划
2. 提供动作指导，包括动作要领、常见错误和注意事项
3. 根据用户的反馈调整训练计划
4. 给出训练建议和激励

## 你的原则
- 安全第一：始终强调正确姿势和循序渐进
- 个性化：根据用户的实际情况定制方案
- 科学性：基于运动科学原理给出建议
- 可执行性：确保建议切实可行

## 工具使用
- 生成训练计划时使用 generate_workout_plan 工具
- 查询动作详情时使用 get_exercise_info 工具
- 计算身体指标时使用 calculate_bmi 工具

## 回复风格
- 专业但易懂，避免过多术语
- 结构清晰，使用列表和分点
- 必要时提供示例和比喻
- 语气鼓励积极，但不过度
"""


class FitnessCoachAgent(BaseAgent):
    """健身教练 Agent"""

    def __init__(self, llm_client: Any = None, memory: Any = None):
        super().__init__(
            name="FitnessCoach",
            role=AgentRole.FITNESS_COACH,
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

        # 添加用户消息
        self.add_message("user", message)

        # 构建上下文
        user_context = self._build_context(context)

        # 调用 LLM
        try:
            tools = self.get_tool_schemas()
            messages = self.get_messages_for_api()

            # 某些网关/模型不支持 tools 时会返回 400，降级到普通对话避免整链路失败。
            try:
                response = self.llm.chat_with_tools(
                    message=messages[-1]["content"],
                    tools=tools,
                    system=self.get_system_prompt() + user_context
                )
            except Exception as tool_exc:
                if "400" in str(tool_exc):
                    fallback_content = self.llm.chat(
                        message=messages[-1]["content"],
                        system=self.get_system_prompt() + user_context
                    )
                    self.add_message("assistant", fallback_content)
                    self.state = "done"
                    return AgentResponse(content=fallback_content, done=True)
                raise

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            # 处理工具调用
            if tool_calls:
                tool_results = self._handle_tool_calls(tool_calls)
                # 将工具结果加入消息
                for tc, result in zip(tool_calls, tool_results):
                    self.add_message("assistant", content)
                    # 简化：将工具结果作为系统消息
                    self.add_message("system", f"工具 {tc['name']} 执行结果: {result}")

                # 再次调用 LLM 获取最终回复
                final_response = self.llm.chat(
                    message="请根据工具执行结果，给用户一个完整的回复。",
                    system=self.get_system_prompt() + user_context
                )
                content = final_response

            # 添加助手回复
            self.add_message("assistant", content)

            self.state = "done"
            return AgentResponse(content=content, done=True)

        except Exception as e:
            self.state = "error"
            return AgentResponse(content=f"处理出错: {str(e)}", done=True)

    def _build_context(self, context: Dict = None) -> str:
        """构建上下文信息"""
        if not context:
            return ""

        lines = ["\n## 当前用户信息"]
        if "user_profile" in context:
            profile = context["user_profile"]
            lines.append(f"- 健身目标: {profile.get('fitness_goals', '未设置')}")
            lines.append(f"- 健身水平: {profile.get('fitness_level', '未设置')}")

        return "\n".join(lines)

    def _handle_tool_calls(self, tool_calls: List[Dict]) -> List[str]:
        """处理工具调用"""
        results = []
        for tc in tool_calls:
            tool_call = ToolCall(
                id=tc.get("id", ""),
                name=tc.get("name", ""),
                arguments=tc.get("arguments", {})
            )
            result = self.tool_executor.execute(tool_call)
            results.append(result)
        return results

    def generate_workout_plan(
        self,
        goal: str,
        level: str,
        days_per_week: int,
        minutes_per_day: int,
        **kwargs
    ) -> Dict:
        """直接生成训练计划"""
        result = tool_registry.execute(
            "generate_workout_plan",
            goal=goal,
            level=level,
            days_per_week=days_per_week,
            minutes_per_day=minutes_per_day,
            **kwargs
        )
        return result.data if result.success else {"error": result.error}
