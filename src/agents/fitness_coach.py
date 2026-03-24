"""
Fitness Coach Agent

健身教练 Agent，负责训练计划生成、动作指导等。
"""
from typing import Any, Dict, List, Optional
import re
from .base import BaseAgent, AgentRole, AgentResponse, ToolCall, ToolExecutor
from ..tools import registry as tool_registry
from ..services.llm_client import extract_compat_tool_calls


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

        direct_plan = self._try_direct_workout_plan(message)
        if direct_plan is not None:
            self.add_message("assistant", direct_plan)
            self.state = "done"
            return AgentResponse(content=direct_plan, done=True)

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
                    compat = extract_compat_tool_calls(fallback_content)
                    if compat["tool_calls"]:
                        tool_results = self._handle_tool_calls(compat["tool_calls"])
                        for tc, result in zip(compat["tool_calls"], tool_results):
                            self.add_message("assistant", compat["content"] or "我来帮你处理这个请求。")
                            self.add_message("system", f"工具 {tc['name']} 执行结果: {result}")

                        final_response = self.llm.chat(
                            message="请根据工具执行结果，给用户一个完整回复。不要输出任何 XML 或 tool_call 标签。",
                            system=self.get_system_prompt() + user_context
                        )
                        clean_content = extract_compat_tool_calls(final_response)["content"] or final_response
                        self.add_message("assistant", clean_content)
                        self.state = "done"
                        return AgentResponse(content=clean_content, done=True)

                    clean_fallback = compat["content"] or fallback_content
                    self.add_message("assistant", clean_fallback)
                    self.state = "done"
                    return AgentResponse(content=clean_fallback, done=True)
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
            content = extract_compat_tool_calls(content)["content"] or content
            self.add_message("assistant", content)

            self.state = "done"
            return AgentResponse(content=content, done=True)

        except Exception as e:
            self.state = "error"
            return AgentResponse(content=f"处理出错: {str(e)}", done=True)

    def _try_direct_workout_plan(self, message: str) -> Optional[str]:
        text = (message or "").lower()
        trigger_words = ["计划", "我的计划", "计划呢", "增肌", "减脂", "塑形", "训练"]
        if not any(word in text for word in trigger_words):
            return None

        goal = "增肌" if "增肌" in text else ("减脂" if "减脂" in text else None)
        if goal is None:
            return None

        days = 4
        m_days_range = re.search(r"(\d)\s*[-~到至]\s*(\d)\s*天", text)
        m_days_single = re.search(r"每周\s*(\d)\s*天", text)
        if m_days_range:
            days = max(2, min(6, int(m_days_range.group(1))))
        elif m_days_single:
            days = max(2, min(6, int(m_days_single.group(1))))
        elif "每天" in text:
            days = 6

        level = "中级" if days >= 5 else "初学者"
        minutes = 60 if days >= 5 else 45

        result = tool_registry.execute(
            "generate_workout_plan",
            goal=goal,
            level=level,
            days_per_week=days,
            minutes_per_day=minutes,
        )
        if not result.success:
            return None

        plan = result.data
        sessions = plan.get("sessions", [])
        lines = [
            f"已根据你的信息生成{goal}训练计划：",
            f"- 计划名称：{plan.get('name', goal + '训练计划')}",
            f"- 每周训练：{plan.get('sessions_per_week', days)} 天",
            f"- 建议单次时长：{minutes} 分钟",
            "",
            "本周安排（示例）：",
        ]
        for session in sessions[:min(5, len(sessions))]:
            lines.append(f"- 第{session.get('day')}天：{session.get('name')}（{session.get('duration_minutes')} 分钟）")

        lines.append("")
        lines.append("如果你愿意，我下一条可以把每天的动作、组数和强度写成可直接照做的打卡版。")
        return "\n".join(lines)

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
