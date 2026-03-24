"""
Workout related tools
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from .base import Tool, ToolResult, registry
from ..models import MuscleGroup, ExerciseType, Difficulty


class GenerateWorkoutPlanTool(Tool):
    """生成训练计划工具"""

    name = "generate_workout_plan"
    description = "根据用户目标生成个性化训练计划"
    parameters_schema = {
        "goal": {
            "type": "string",
            "description": "训练目标: 减脂/增肌/保持/提升耐力/提升力量/综合健身",
            "required": True
        },
        "level": {
            "type": "string",
            "description": "健身水平: 初学者/中级/高级",
            "required": True
        },
        "days_per_week": {
            "type": "integer",
            "description": "每周训练天数 (1-7)",
            "required": True
        },
        "minutes_per_day": {
            "type": "integer",
            "description": "每天训练时长(分钟)",
            "required": True
        },
        "focus_areas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "重点训练部位列表"
        },
        "injuries": {
            "type": "array",
            "items": {"type": "string"},
            "description": "伤病情况列表，需要避免的动作"
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        goal = self._normalize_goal(kwargs.get("goal", "综合健身"))
        level = self._normalize_level(kwargs.get("level", "初学者"))
        days = min(max(kwargs.get("days_per_week", 3), 1), 7)
        minutes = max(int(kwargs.get("minutes_per_day", 60)), 10)
        focus = kwargs.get("focus_areas", [])
        injuries = kwargs.get("injuries", [])

        # 基于目标生成计划结构
        plan = self._build_plan(goal, level, days, minutes, focus, injuries)

        return ToolResult(success=True, data=plan)

    def _normalize_goal(self, value: str) -> str:
        text = (value or "").strip().lower()
        mapping = {
            "fat_loss": "减脂",
            "lose_weight": "减脂",
            "减脂": "减脂",
            "muscle_gain": "增肌",
            "gain_muscle": "增肌",
            "增肌": "增肌",
            "maintain": "保持",
            "保持": "保持",
            "endurance": "提升耐力",
            "提升耐力": "提升耐力",
            "strength": "提升力量",
            "提升力量": "提升力量",
            "general": "综合健身",
            "综合健身": "综合健身",
        }
        return mapping.get(text, value if value else "综合健身")

    def _normalize_level(self, value: str) -> str:
        text = (value or "").strip().lower()
        mapping = {
            "beginner": "初学者",
            "初学者": "初学者",
            "intermediate": "中级",
            "中级": "中级",
            "advanced": "高级",
            "高级": "高级",
        }
        return mapping.get(text, "初学者")

    def _build_plan(self, goal: str, level: str, days: int,
                    minutes: int, focus: List[str], injuries: List[str]) -> Dict:
        """构建训练计划"""
        plan = {
            "name": f"{goal}训练计划",
            "duration_weeks": 4,
            "sessions_per_week": days,
            "sessions": []
        }

        # 根据训练天数分配肌群
        split_patterns = {
            1: [["全身"]],
            2: [["上肢"], ["下肢"]],
            3: [["胸", "三头"], ["背", "二头"], ["腿", "肩"]],
            4: [["胸"], ["背"], ["腿"], ["肩", "手臂"]],
            5: [["胸"], ["背"], ["腿"], ["肩"], ["手臂", "核心"]],
            6: [["胸"], ["背"], ["腿"], ["肩"], ["手臂"], ["核心", "有氧"]],
            7: [["胸"], ["背"], ["腿"], ["肩"], ["手臂"], ["核心"], ["有氧"]]
        }

        pattern = split_patterns.get(days, split_patterns[3])

        for i, muscles in enumerate(pattern):
            session = {
                "day": i + 1,
                "name": self._get_session_name(muscles),
                "duration_minutes": minutes,
                "muscles": muscles,
                "exercises": self._get_exercises(muscles, level, injuries),
                "warmup": self._get_warmup(level),
                "cooldown": self._get_cooldown()
            }
            plan["sessions"].append(session)

        return plan

    def _get_session_name(self, muscles: List[str]) -> str:
        names = {
            "全身": "全身训练",
            "上肢": "上肢训练",
            "下肢": "下肢训练",
            "胸": "胸部训练",
            "背": "背部训练",
            "腿": "腿部训练",
            "肩": "肩部训练",
            "手臂": "手臂训练",
            "核心": "核心训练",
            "有氧": "有氧训练"
        }
        return names.get(muscles[0], f"{muscles[0]}训练")

    def _get_exercises(self, muscles: List[str], level: str,
                       injuries: List[str]) -> List[Dict]:
        """获取动作列表"""
        # 简化的动作库
        exercise_db = {
            "胸": [
                {"name": "俯卧撑", "sets": 3, "reps": "12-15", "difficulty": "简单"},
                {"name": "哑铃卧推", "sets": 4, "reps": "8-12", "difficulty": "中等"},
                {"name": "上斜卧推", "sets": 3, "reps": "10-12", "difficulty": "中等"},
            ],
            "背": [
                {"name": "引体向上", "sets": 3, "reps": "6-10", "difficulty": "困难"},
                {"name": "哑铃划船", "sets": 4, "reps": "10-12", "difficulty": "中等"},
                {"name": "高位下拉", "sets": 3, "reps": "12-15", "difficulty": "简单"},
            ],
            "腿": [
                {"name": "深蹲", "sets": 4, "reps": "8-12", "difficulty": "中等"},
                {"name": "箭步蹲", "sets": 3, "reps": "10-12", "difficulty": "中等"},
                {"name": "腿举", "sets": 3, "reps": "12-15", "difficulty": "简单"},
            ],
            "肩": [
                {"name": "哑铃推举", "sets": 4, "reps": "8-12", "difficulty": "中等"},
                {"name": "侧平举", "sets": 3, "reps": "12-15", "difficulty": "简单"},
                {"name": "前平举", "sets": 3, "reps": "12-15", "difficulty": "简单"},
            ],
            "核心": [
                {"name": "平板支撑", "sets": 3, "reps": "30-60秒", "difficulty": "简单"},
                {"name": "卷腹", "sets": 3, "reps": "15-20", "difficulty": "简单"},
                {"name": "俄罗斯转体", "sets": 3, "reps": "20", "difficulty": "中等"},
            ],
            "有氧": [
                {"name": "跑步", "sets": 1, "reps": "20-30分钟", "difficulty": "简单"},
                {"name": "跳绳", "sets": 3, "reps": "5分钟", "difficulty": "中等"},
            ]
        }

        exercises = []
        for muscle in muscles:
            if muscle in exercise_db:
                for ex in exercise_db[muscle]:
                    # 过滤不适合伤病的动作
                    if not self._is_contraindicated(ex["name"], injuries):
                        exercises.append(ex)

        # 根据水平调整
        if level == "初学者":
            exercises = [e for e in exercises if e["difficulty"] in ["简单", "中等"]]
        elif level == "高级":
            # 保留所有动作
            pass

        return exercises[:6]  # 最多6个动作

    def _is_contraindicated(self, exercise: str, injuries: List[str]) -> bool:
        """检查动作是否与伤病冲突"""
        contraindications = {
            "膝盖": ["深蹲", "箭步蹲", "腿举"],
            "肩膀": ["推举", "卧推", "肩推"],
            "腰部": ["硬拉", "划船", "深蹲"],
            "手腕": ["俯卧撑", "卧推", "推举"]
        }

        for injury in injuries:
            if injury in contraindications:
                if exercise in contraindications[injury]:
                    return True
        return False

    def _get_warmup(self, level: str) -> List[str]:
        """热身动作"""
        return ["动态拉伸 5分钟", "关节活动", "轻度有氧 3-5分钟"]

    def _get_cooldown(self) -> List[str]:
        """放松动作"""
        return ["静态拉伸 5-10分钟", "泡沫轴放松"]


class GetExerciseInfoTool(Tool):
    """获取动作详细信息工具"""

    name = "get_exercise_info"
    description = "获取健身动作的详细指导信息，包括动作要领、常见错误、注意事项"
    parameters_schema = {
        "exercise_name": {
            "type": "string",
            "description": "动作名称",
            "required": True
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get("exercise_name", "")

        # 动作知识库
        exercise_knowledge = {
            "深蹲": {
                "name": "深蹲",
                "target_muscles": ["股四头肌", "臀大肌", "腘绳肌"],
                "instructions": [
                    "双脚与肩同宽或略宽，脚尖微微外展",
                    "核心收紧，胸部挺起，视线向前",
                    "先屈髋后屈膝，臀部向后坐",
                    "下蹲至大腿与地面平行或略低",
                    "膝盖与脚尖方向一致，不要内扣",
                    "发力时臀部和腿部同时用力站起"
                ],
                "common_mistakes": [
                    "膝盖内扣 - 容易造成膝关节损伤",
                    "弯腰驼背 - 增加腰椎压力",
                    "重心前移 - 脚跟抬起",
                    "下蹲深度不够 - 效果打折"
                ],
                "tips": ["初学者可以先做徒手深蹲", "有膝盖问题者注意控制深度"],
                "breathing": "下蹲吸气，站起呼气"
            },
            "俯卧撑": {
                "name": "俯卧撑",
                "target_muscles": ["胸大肌", "三角肌前束", "肱三头肌"],
                "instructions": [
                    "双手略宽于肩，手指向前",
                    "身体呈一条直线，核心收紧",
                    "下降时肘部约45度角外展",
                    "胸部接近地面后推起",
                    "全程保持身体稳定不塌腰"
                ],
                "common_mistakes": [
                    "塌腰 - 核心没有收紧",
                    "撅臀 - 身体不成直线",
                    "肘部过度外展 - 肩关节压力大",
                    "下降幅度不够"
                ],
                "tips": ["做不了标准俯卧撑可以做跪姿俯卧撑", "手腕有不适可握拳支撑"],
                "breathing": "下降吸气，推起呼气"
            },
            "硬拉": {
                "name": "硬拉",
                "target_muscles": ["竖脊肌", "臀大肌", "腘绳肌", "斜方肌"],
                "instructions": [
                    "双脚与髋同宽，杠铃在脚正上方",
                    "屈髋屈膝握住杠铃，背部保持挺直",
                    "核心收紧，肩胛骨后缩",
                    "蹬地伸髋伸膝，将杠铃沿腿上拉",
                    "顶峰时臀部收缩，身体站直",
                    "下放时控制速度，背部保持挺直"
                ],
                "common_mistakes": [
                    "弯腰起拉 - 极危险，腰椎压力大",
                    "先伸膝再伸髋 - 变成蹲拉",
                    "杠铃离身体太远 - 增加腰椎力矩",
                    "过度伸展 - 顶峰后仰"
                ],
                "tips": ["初学者建议从轻重量开始学习动作模式", "可以使用六角杠减少腰椎压力"],
                "breathing": "拉起前吸气并憋气，站直后呼气"
            }
        }

        if name in exercise_knowledge:
            return ToolResult(success=True, data=exercise_knowledge[name])

        # 返回通用信息
        return ToolResult(success=True, data={
            "name": name,
            "instructions": ["请咨询专业教练获取详细指导"],
            "note": "该动作暂未收录详细指导信息"
        })


# 注册工具
registry.register(GenerateWorkoutPlanTool())
registry.register(GetExerciseInfoTool())
