"""
Body data related tools
"""
from typing import Dict, Any, List
from .base import Tool, ToolResult, registry


class CalculateBMITool(Tool):
    """BMI计算工具"""

    name = "calculate_bmi"
    description = "计算BMI并给出健康评估"
    parameters_schema = {
        "height": {
            "type": "number",
            "description": "身高(cm)",
            "required": True
        },
        "weight": {
            "type": "number",
            "description": "体重(kg)",
            "required": True
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        height = kwargs.get("height", 170)
        weight = kwargs.get("weight", 70)

        height_m = height / 100
        bmi = weight / (height_m ** 2)

        # 分类和建议
        if bmi < 18.5:
            category = "偏瘦"
            advice = "建议适当增加热量摄入，结合力量训练增加肌肉量"
            health_risk = "可能存在营养不良风险"
        elif bmi < 24:
            category = "正常"
            advice = "保持现有体重，继续健康饮食和规律运动"
            health_risk = "健康风险较低"
        elif bmi < 28:
            category = "偏胖"
            advice = "建议控制饮食热量，增加有氧运动"
            health_risk = "存在一定健康风险，建议减重"
        else:
            category = "肥胖"
            advice = "建议在专业指导下进行减重，控制饮食并增加运动"
            health_risk = "健康风险较高，建议尽快采取行动"

        # 理想体重范围
        ideal_min = 18.5 * (height_m ** 2)
        ideal_max = 24 * (height_m ** 2)

        result = {
            "bmi": round(bmi, 2),
            "category": category,
            "ideal_weight_range": {
                "min": round(ideal_min, 1),
                "max": round(ideal_max, 1)
            },
            "weight_to_ideal": round(weight - (ideal_min + ideal_max) / 2, 1),
            "advice": advice,
            "health_risk": health_risk
        }

        return ToolResult(success=True, data=result)


class TrackBodyProgressTool(Tool):
    """身体进度追踪工具"""

    name = "track_body_progress"
    description = "记录和分析身体数据变化趋势"
    parameters_schema = {
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "weight": {"type": "number"},
                    "body_fat": {"type": "number"}
                }
            },
            "description": "身体数据记录列表",
            "required": True
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        records = kwargs.get("records", [])

        if len(records) < 2:
            return ToolResult(
                success=True,
                data={"message": "数据记录不足，至少需要2条记录才能分析趋势"}
            )

        # 按日期排序
        sorted_records = sorted(records, key=lambda x: x.get("date", ""))

        # 计算变化趋势
        first = sorted_records[0]
        last = sorted_records[-1]

        weight_change = last.get("weight", 0) - first.get("weight", 0)
        body_fat_change = (last.get("body_fat", 0) - first.get("body_fat", 0))

        # 周平均变化
        days = len(sorted_records) * 7  # 假设每周记录一次
        weeks = max(days / 7, 1)
        weekly_weight_change = weight_change / weeks

        # 趋势判断
        if weight_change < -0.5:
            trend = "减重中"
            trend_emoji = "📉"
        elif weight_change > 0.5:
            trend = "增重中"
            trend_emoji = "📈"
        else:
            trend = "稳定"
            trend_emoji = "➡️"

        # 预测
        prediction = None
        if abs(weekly_weight_change) > 0.1:
            target_weight = 65  # 假设目标体重
            weeks_to_target = abs(last.get("weight", 70) - target_weight) / abs(weekly_weight_change)
            prediction = {
                "weekly_change": round(weekly_weight_change, 2),
                "weeks_to_target": round(weeks_to_target, 1)
            }

        result = {
            "period": {
                "start": first.get("date"),
                "end": last.get("date"),
                "weeks": round(weeks)
            },
            "changes": {
                "weight": round(weight_change, 2),
                "body_fat": round(body_fat_change, 2)
            },
            "trend": trend,
            "analysis": self._analyze_progress(weight_change, body_fat_change),
            "prediction": prediction
        }

        return ToolResult(success=True, data=result)

    def _analyze_progress(self, weight_change: float, body_fat_change: float) -> str:
        """分析进度并给出反馈"""
        if weight_change < 0 and body_fat_change < 0:
            return "很好！体重和体脂都在下降，减脂进展顺利"
        elif weight_change < 0 and body_fat_change > 0:
            return "体重下降但体脂上升，可能是在流失肌肉，建议增加蛋白质摄入和力量训练"
        elif weight_change > 0 and body_fat_change < 0:
            return "很棒！体重增加但体脂下降，这是理想的增肌状态"
        elif weight_change > 0 and body_fat_change > 0:
            return "体重和体脂都在增加，如果是增肌期需要关注体脂控制"
        else:
            return "数据变化较小，保持当前状态"


class CalculateBodyFatTool(Tool):
    """体脂率计算工具 (使用海军法)"""

    name = "calculate_body_fat"
    description = "使用围度测量法计算体脂率 (海军法)"
    parameters_schema = {
        "gender": {
            "type": "string",
            "description": "性别: 男/女",
            "required": True
        },
        "height": {
            "type": "number",
            "description": "身高(cm)",
            "required": True
        },
        "waist": {
            "type": "number",
            "description": "腰围(cm)",
            "required": True
        },
        "neck": {
            "type": "number",
            "description": "颈围(cm)",
            "required": True
        },
        "hip": {
            "type": "number",
            "description": "臀围(cm)，女性必填"
        }
    }

    def execute(self, **kwargs) -> ToolResult:
        gender = self._normalize_gender(kwargs.get("gender", "男"))
        height = kwargs.get("height", 170)
        waist = kwargs.get("waist", 80)
        neck = kwargs.get("neck", 35)
        hip = kwargs.get("hip", 90)

        import math

        if height <= 0 or waist <= 0 or neck <= 0:
            return ToolResult(success=False, error="身高、腰围、颈围必须为正数")

        if gender == "男" and waist <= neck:
            return ToolResult(success=False, error="男性参数非法：腰围需大于颈围")

        if gender == "女" and not hip:
            return ToolResult(success=False, error="女性需要提供臀围数据")

        if gender == "女" and (waist + hip - neck) <= 0:
            return ToolResult(success=False, error="女性参数非法：腰围+臀围需大于颈围")

        if gender == "男":
            # 男性公式
            body_fat = 495 / (
                1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height)
            ) - 450
        else:
            # 女性公式
            body_fat = 495 / (
                1.29579 - 0.35004 * math.log10(waist + hip - neck) + 0.22100 * math.log10(height)
            ) - 450

        # 体脂分类
        if gender == "男":
            if body_fat < 6:
                category = "过低"
            elif body_fat < 14:
                category = "运动员"
            elif body_fat < 18:
                category = "健康"
            elif body_fat < 25:
                category = "可接受"
            else:
                category = "偏高"
        else:
            if body_fat < 14:
                category = "过低"
            elif body_fat < 21:
                category = "运动员"
            elif body_fat < 25:
                category = "健康"
            elif body_fat < 32:
                category = "可接受"
            else:
                category = "偏高"

        result = {
            "body_fat_percent": round(body_fat, 1),
            "category": category,
            "gender": gender,
            "measurements": {
                "waist": waist,
                "neck": neck,
                "hip": hip if gender == "女" else None
            }
        }

        return ToolResult(success=True, data=result)

    def _normalize_gender(self, value: str) -> str:
        """Normalize gender values to 中文男/女。"""
        text = (value or "").strip().lower()
        male_aliases = {"男", "male", "m", "man", "boy"}
        female_aliases = {"女", "female", "f", "woman", "girl"}

        if text in male_aliases:
            return "男"
        if text in female_aliases:
            return "女"

        # 默认按男性处理，保证向后兼容
        return "男"


# 注册工具
registry.register(CalculateBMITool())
registry.register(TrackBodyProgressTool())
registry.register(CalculateBodyFatTool())
