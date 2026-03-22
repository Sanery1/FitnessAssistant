"""
Nutrition related tools
"""
from typing import Dict, Any, List
from .base import Tool, ToolResult, registry


class CalculateCaloriesTool(Tool):
    """计算热量需求工具"""

    name = "calculate_calories"
    description = "根据用户信息计算每日热量需求和宏量营养素分配"
    parameters_schema = {
        "gender": {
            "type": "string",
            "description": "性别: 男/女",
            "required": True
        },
        "age": {
            "type": "integer",
            "description": "年龄",
            "required": True
        },
        "height": {
            "type": "number",
            "description": "身高(cm)",
            "required": True
        },
        "weight": {
            "type": "number",
            "description": "体重(kg)",
            "required": True
        },
        "activity_level": {
            "type": "string",
            "description": "活动水平: 久坐/轻度活动/中度活动/高度活动/极高活动"
        },
        "goal": {
            "type": "string",
            "description": "目标: 减脂/增肌/保持"
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        gender = kwargs.get("gender", "男")
        age = kwargs.get("age", 25)
        height = kwargs.get("height", 170)
        weight = kwargs.get("weight", 70)
        activity = kwargs.get("activity_level", "中度活动")
        goal = kwargs.get("goal", "保持")

        # Mifflin-St Jeor 公式计算基础代谢
        if gender == "男":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # 活动系数
        activity_factors = {
            "久坐": 1.2,
            "轻度活动": 1.375,
            "中度活动": 1.55,
            "高度活动": 1.725,
            "极高活动": 1.9
        }
        tdee = bmr * activity_factors.get(activity, 1.55)

        # 根据目标调整
        goal_adjustments = {
            "减脂": -500,
            "增肌": 300,
            "保持": 0
        }
        target_calories = tdee + goal_adjustments.get(goal, 0)

        # 宏量营养素分配
        macros = self._calculate_macros(target_calories, goal)

        result = {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "target_calories": round(target_calories),
            "macros": macros,
            "goal": goal,
            "tips": self._get_tips(goal)
        }

        return ToolResult(success=True, data=result)

    def _calculate_macros(self, calories: float, goal: str) -> Dict:
        """计算宏量营养素"""
        if goal == "减脂":
            # 高蛋白，中碳水
            protein_ratio = 0.35
            carbs_ratio = 0.35
            fat_ratio = 0.30
        elif goal == "增肌":
            # 中蛋白，高碳水
            protein_ratio = 0.30
            carbs_ratio = 0.45
            fat_ratio = 0.25
        else:
            # 均衡
            protein_ratio = 0.30
            carbs_ratio = 0.40
            fat_ratio = 0.30

        return {
            "protein": {
                "grams": round(calories * protein_ratio / 4),
                "calories": round(calories * protein_ratio),
                "ratio": protein_ratio
            },
            "carbs": {
                "grams": round(calories * carbs_ratio / 4),
                "calories": round(calories * carbs_ratio),
                "ratio": carbs_ratio
            },
            "fat": {
                "grams": round(calories * fat_ratio / 9),
                "calories": round(calories * fat_ratio),
                "ratio": fat_ratio
            }
        }

    def _get_tips(self, goal: str) -> List[str]:
        """获取营养建议"""
        tips = {
            "减脂": [
                "保持热量缺口，但不要低于基础代谢",
                "高蛋白饮食有助于保持肌肉量",
                "选择低GI碳水，控制血糖波动",
                "增加膳食纤维摄入，增强饱腹感"
            ],
            "增肌": [
                "热量盈余控制在300-500卡",
                "训练后补充蛋白质和碳水",
                "分多餐进食，每餐30-40g蛋白质",
                "充足睡眠促进肌肉恢复"
            ],
            "保持": [
                "保持均衡饮食",
                "注意微量营养素摄入",
                "保持规律进餐时间",
                "多喝水，保持身体水分"
            ]
        }
        return tips.get(goal, [])


class AnalyzeNutritionTool(Tool):
    """营养分析工具"""

    name = "analyze_nutrition"
    description = "分析用户饮食记录，给出营养评估和改进建议"
    parameters_schema = {
        "foods": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "amount": {"type": "number"},
                    "unit": {"type": "string"}
                }
            },
            "description": "食物列表",
            "required": True
        },
        "target_calories": {
            "type": "number",
            "description": "目标热量"
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        foods = kwargs.get("foods", [])
        target = kwargs.get("target_calories", 2000)

        # 简化的食物营养数据
        food_db = {
            "米饭": {"cal": 116, "p": 2.6, "c": 25.6, "f": 0.3},
            "面条": {"cal": 137, "p": 4.5, "c": 28.5, "f": 0.5},
            "鸡胸肉": {"cal": 133, "p": 23.3, "c": 0, "f": 2.5},
            "牛肉": {"cal": 166, "p": 20, "c": 0, "f": 9},
            "鸡蛋": {"cal": 144, "p": 13.3, "c": 1.3, "f": 9.5},
            "牛奶": {"cal": 54, "p": 3, "c": 4.6, "f": 3.2},
            "西兰花": {"cal": 33, "p": 3.2, "c": 4.4, "f": 0.3},
            "苹果": {"cal": 52, "p": 0.3, "c": 13.8, "f": 0.2},
            "香蕉": {"cal": 89, "p": 1.1, "c": 22.8, "f": 0.3}
        }

        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        details = []

        for food in foods:
            name = food.get("name", "")
            amount = food.get("amount", 100)

            if name in food_db:
                data = food_db[name]
                multiplier = amount / 100

                item = {
                    "name": name,
                    "amount": amount,
                    "calories": round(data["cal"] * multiplier),
                    "protein": round(data["p"] * multiplier, 1),
                    "carbs": round(data["c"] * multiplier, 1),
                    "fat": round(data["f"] * multiplier, 1)
                }
                details.append(item)

                total["calories"] += item["calories"]
                total["protein"] += item["protein"]
                total["carbs"] += item["carbs"]
                total["fat"] += item["fat"]

        # 评估
        calorie_diff = total["calories"] - target
        evaluation = {
            "total": total,
            "details": details,
            "target": target,
            "difference": round(calorie_diff),
            "status": "达标" if abs(calorie_diff) < 200 else ("超标" if calorie_diff > 0 else "不足"),
            "recommendations": self._get_recommendations(total, target)
        }

        return ToolResult(success=True, data=evaluation)

    def _get_recommendations(self, total: Dict, target: float) -> List[str]:
        """生成改进建议"""
        recs = []
        diff = total["calories"] - target

        if diff > 300:
            recs.append(f"热量超标{diff}卡，建议减少主食或油脂摄入")
        elif diff < -300:
            recs.append(f"热量不足{abs(diff)}卡，可以适当增加优质蛋白")

        # 蛋白质评估
        protein_target = target * 0.3 / 4  # 30%来自蛋白质
        if total["protein"] < protein_target * 0.8:
            recs.append("蛋白质摄入偏低，建议增加鸡胸肉、鸡蛋、牛奶等")

        return recs if recs else ["营养摄入基本合理，继续保持！"]


# 注册工具
registry.register(CalculateCaloriesTool())
registry.register(AnalyzeNutritionTool())
