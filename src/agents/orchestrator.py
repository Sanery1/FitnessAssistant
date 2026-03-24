"""
Orchestrator Agent

主控编排 Agent，负责协调其他 Agent，处理用户请求路由。
"""
from typing import Any, Dict, List, Optional
import re
from enum import Enum
from .base import BaseAgent, AgentRole, AgentResponse
from .fitness_coach import FitnessCoachAgent
from .nutritionist import NutritionistAgent
from .data_analyst import DataAnalystAgent


class QueryType(str, Enum):
    """查询类型"""
    WORKOUT = "workout"      # 训练相关
    NUTRITION = "nutrition"  # 营养相关
    DATA = "data"           # 数据分析
    GENERAL = "general"      # 通用问题
    MULTI = "multi"         # 多领域问题


SYSTEM_PROMPT = """你是健身助手的智能协调器，负责理解用户需求并分配给合适的专家处理。

## 可用的专家
1. **健身教练** (FitnessCoach): 训练计划、动作指导、训练建议
2. **营养师** (Nutritionist): 饮食建议、热量计算、营养分析
3. **数据分析师** (DataAnalyst): 进度追踪、数据分析、趋势预测

## 你的职责
1. 理解用户的真实意图
2. 判断应该由哪个专家处理
3. 协调多个专家处理复杂问题
4. 整合回复给用户

## 路由规则
- 训练、动作、计划相关 → 健身教练
- 饮食、营养、热量相关 → 营养师
- 数据、进度、趋势相关 → 数据分析师
- 涉及多个领域 → 协调多个专家

## 回复风格
- 简洁明了，直接回答或说明将调用哪个专家
- 不要重复专家的内容
- 保持对话流畅
"""


class OrchestratorAgent(BaseAgent):
    """主控编排 Agent"""

    def __init__(self, llm_client: Any = None, memory: Any = None):
        super().__init__(
            name="Orchestrator",
            role=AgentRole.ORCHESTRATOR,
            llm_client=llm_client,
            tools=None,
            memory=memory
        )

        # 初始化专家 Agent
        self.experts = {
            "fitness_coach": FitnessCoachAgent(llm_client, memory),
            "nutritionist": NutritionistAgent(llm_client, memory),
            "data_analyst": DataAnalystAgent(llm_client, memory)
        }

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def classify_query(self, message: str, context: Optional[Dict] = None) -> QueryType:
        """分类用户查询"""
        message_lower = message.lower()

        # 训练相关关键词
        workout_keywords = ["训练", "健身", "动作", "计划", "锻炼", "肌肉", "力量", "有氧", "深蹲", "卧推", "引体"]
        # 营养相关关键词
        nutrition_keywords = ["饮食", "营养", "热量", "蛋白质", "碳水", "脂肪", "吃", "餐", "减肥", "增肌餐"]
        # 数据相关关键词
        data_keywords = ["数据", "进度", "趋势", "体重", "体脂", "bmi", "分析", "记录", "变化"]

        is_workout = any(kw in message_lower for kw in workout_keywords)
        is_nutrition = any(kw in message_lower for kw in nutrition_keywords)
        is_data = any(kw in message_lower for kw in data_keywords)

        # 当消息主要是“补充身体参数”时，优先继承最近一次明确意图，避免会话跑偏。
        if self._looks_like_profile_update(message_lower):
            inherited = self._infer_query_type_from_context(context)
            if inherited is not None:
                return inherited

        if sum([is_workout, is_nutrition, is_data]) > 1:
            return QueryType.MULTI
        elif is_workout:
            return QueryType.WORKOUT
        elif is_nutrition:
            return QueryType.NUTRITION
        elif is_data:
            return QueryType.DATA
        else:
            return QueryType.GENERAL

    def _looks_like_profile_update(self, message_lower: str) -> bool:
        has_age = bool(re.search(r"\d+\s*岁", message_lower))
        has_weight = bool(re.search(r"\d+(?:\.\d+)?\s*kg", message_lower))
        has_height = bool(re.search(r"\d+(?:\.\d+)?\s*cm", message_lower))
        has_gender = ("男" in message_lower) or ("女" in message_lower)
        has_days = bool(re.search(r"\d+\s*[-~到至]?\s*\d*\s*天", message_lower))
        return sum([has_age, has_weight, has_height, has_gender, has_days]) >= 2

    def _infer_query_type_from_context(self, context: Optional[Dict]) -> Optional[QueryType]:
        if not context:
            return None
        session = context.get("session_context") or {}
        messages = session.get("messages") or []
        for item in reversed(messages):
            if item.get("role") != "user":
                continue
            text = (item.get("content") or "").lower()
            if not text:
                continue

            if any(k in text for k in ["热量", "营养", "饮食", "卡路里", "宏量", "蛋白质", "减脂餐", "增肌餐"]):
                return QueryType.NUTRITION
            if any(k in text for k in ["训练", "计划", "动作", "健身", "增肌", "减脂", "塑形", "我的计划", "计划呢"]):
                return QueryType.WORKOUT
            if any(k in text for k in ["数据", "进度", "趋势", "体脂", "bmi"]):
                return QueryType.DATA
        return None

    def process(self, message: str, context: Dict = None) -> AgentResponse:
        """处理用户消息 - 路由到合适的专家"""
        self.state = "thinking"
        self.add_message("user", message)

        # 分类查询
        query_type = self.classify_query(message, context)

        # 路由到专家
        expert_response = self._route_to_expert(query_type, message, context)

        # 整合回复
        self.add_message("assistant", expert_response.content)
        self.state = "done"

        return expert_response

    def _route_to_expert(
        self,
        query_type: QueryType,
        message: str,
        context: Dict = None
    ) -> AgentResponse:
        """路由到专家"""
        if query_type == QueryType.WORKOUT:
            return self.experts["fitness_coach"].process(message, context)
        elif query_type == QueryType.NUTRITION:
            return self.experts["nutritionist"].process(message, context)
        elif query_type == QueryType.DATA:
            return self.experts["data_analyst"].process(message, context)
        elif query_type == QueryType.MULTI:
            # 多专家协作
            return self._multi_expert_process(message, context)
        else:
            # 通用问题，使用健身教练作为默认
            return self.experts["fitness_coach"].process(message, context)

    def _multi_expert_process(self, message: str, context: Dict = None) -> AgentResponse:
        """多专家协作处理"""
        # 简化：依次调用相关专家
        responses = []

        # 先让健身教练处理
        workout_response = self.experts["fitness_coach"].process(message, context)
        responses.append(f"【训练建议】\n{workout_response.content}")

        # 如果涉及营养，也让营养师处理
        if "吃" in message or "营养" in message or "热量" in message:
            nutrition_response = self.experts["nutritionist"].process(message, context)
            responses.append(f"【营养建议】\n{nutrition_response.content}")

        combined = "\n\n".join(responses)
        return AgentResponse(content=combined, done=True)

    def get_expert(self, name: str) -> Optional[BaseAgent]:
        """获取指定专家"""
        return self.experts.get(name)
