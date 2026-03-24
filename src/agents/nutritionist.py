"""
Nutritionist Agent

营养师 Agent，负责营养计算、饮食建议等。
"""
from typing import Any, Dict, List
import re
from .base import BaseAgent, AgentRole, AgentResponse, ToolCall, ToolExecutor
from ..tools import registry as tool_registry
from ..services.llm_client import extract_compat_tool_calls


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

        direct = self._try_direct_calorie_calculation(message)
        if direct is not None:
            self.add_message("assistant", direct)
            self.state = "done"
            return AgentResponse(content=direct, done=True)

        try:
            tools = self.get_tool_schemas()
            messages = self.get_messages_for_api()

            # 某些网关/模型不支持 tools 时会返回 400，降级到普通对话避免整链路失败。
            try:
                response = self.llm.chat_with_tools(
                    message=messages[-1]["content"],
                    tools=tools,
                    system=self.get_system_prompt()
                )
            except Exception as tool_exc:
                if "400" in str(tool_exc):
                    fallback_content = self.llm.chat(
                        message=messages[-1]["content"],
                        system=self.get_system_prompt()
                    )
                    compat = extract_compat_tool_calls(fallback_content)
                    if compat["tool_calls"]:
                        for tc in compat["tool_calls"]:
                            result = self.tool_executor.execute(
                                ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                            )
                            self.add_message("system", f"工具执行结果: {result}")

                        final = self.llm.chat(
                            message="请根据工具结果回复用户。不要输出任何 XML 或 tool_call 标签。",
                            system=self.get_system_prompt()
                        )
                        clean_content = extract_compat_tool_calls(final)["content"] or final
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

            if tool_calls:
                for tc in tool_calls:
                    result = self.tool_executor.execute(
                        ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                    )
                    self.add_message("system", f"工具执行结果: {result}")

                final = self.llm.chat(message="请根据工具结果回复用户", system=self.get_system_prompt())
                content = final

            content = extract_compat_tool_calls(content)["content"] or content
            self.add_message("assistant", content)
            self.state = "done"
            return AgentResponse(content=content, done=True)

        except Exception as e:
            self.state = "error"
            return AgentResponse(content=f"处理出错: {str(e)}", done=True)

    def _try_direct_calorie_calculation(self, message: str) -> Any:
        text = (message or "").lower()
        if not text:
            return None

        # 仅在包含较完整身体信息时触发直算，避免误判普通问答。
        age_m = re.search(r"(\d{1,2})\s*岁", text)
        weight_m = re.search(r"(\d{2,3}(?:\.\d+)?)\s*kg", text)
        height_m = re.search(r"(\d{3}(?:\.\d+)?)\s*cm", text)
        if not (age_m and weight_m and height_m):
            return None

        gender = "男" if "男" in text else ("女" if "女" in text else None)
        if gender is None:
            return None

        if "增肌" in text:
            goal = "增肌"
        elif "减脂" in text or "减重" in text:
            goal = "减脂"
        elif "保持" in text or "维持" in text:
            goal = "保持"
        else:
            goal = "保持"

        activity_level = "中度活动"
        if re.search(r"6\s*[-~到至]?\s*7\s*天", text) or "每天" in text:
            activity_level = "高度活动"
        elif re.search(r"3\s*[-~到至]?\s*5\s*天", text):
            activity_level = "中度活动"
        elif re.search(r"1\s*[-~到至]?\s*3\s*天", text):
            activity_level = "轻度活动"
        elif "久坐" in text:
            activity_level = "久坐"

        result = tool_registry.execute(
            "calculate_calories",
            gender=gender,
            age=int(age_m.group(1)),
            height=float(height_m.group(1)),
            weight=float(weight_m.group(1)),
            activity_level=activity_level,
            goal=goal,
        )

        if not result.success:
            return None

        data = result.data
        lines = [
            "已根据你提供的信息完成热量计算：",
            f"- 目标：{goal}",
            f"- 每日目标热量：{data.get('target_calories')} kcal",
            f"- 基础代谢（BMR）：{data.get('bmr')} kcal",
            f"- 总消耗（TDEE）：{data.get('tdee')} kcal",
            "",
            "建议营养分配：",
            f"- 蛋白质：{data.get('macros', {}).get('protein', {}).get('grams')} g",
            f"- 碳水：{data.get('macros', {}).get('carbs', {}).get('grams')} g",
            f"- 脂肪：{data.get('macros', {}).get('fat', {}).get('grams')} g",
        ]
        tips = data.get("tips") or []
        if tips:
            lines.append("")
            lines.append("补充建议：")
            for tip in tips[:3]:
                lines.append(f"- {tip}")
        return "\n".join(lines)

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
