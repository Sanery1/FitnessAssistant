"""
Edge-case and Negative-path Tests for FastAPI Routes
"""
import sys

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_workout_generate_plan_missing_required_field():
    response = client.post(
        "/api/workout/generate-plan",
        json={
            "goal": "减脂",
            "level": "初学者",
            "minutes_per_day": 45,
        },
    )
    assert response.status_code == 422


def test_workout_generate_plan_wrong_field_type():
    response = client.post(
        "/api/workout/generate-plan",
        json={
            "goal": "减脂",
            "level": "初学者",
            "days_per_week": "three",
            "minutes_per_day": 45,
        },
    )
    assert response.status_code == 422


def test_user_get_not_found():
    response = client.get("/api/user/not_exist_user")
    assert response.status_code == 404


def test_nutrition_calories_wrong_type():
    response = client.post(
        "/api/nutrition/calculate-calories",
        json={
            "gender": "男",
            "age": "twenty",
            "height": 175,
            "weight": 70,
            "activity_level": "中度活动",
            "goal": "减脂",
        },
    )
    assert response.status_code == 422


def test_body_calculate_bmi_missing_field():
    response = client.post(
        "/api/body/calculate-bmi",
        json={"height": 175},
    )
    assert response.status_code == 422


def test_body_fat_accepts_english_gender():
    response = client.post(
        "/api/body/calculate-body-fat",
        json={
            "gender": "male",
            "height": 175,
            "waist": 82,
            "neck": 38,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "body_fat_percent" in data


def test_nutrition_analyze_accepts_weight_alias():
    response = client.post(
        "/api/nutrition/analyze",
        json={
            "foods": [{"name": "鸡胸肉", "weight": 200}],
            "target_calories": 2000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"]["calories"] > 0


def test_cors_preflight_disallowed_method():
    response = client.options(
        "/api/body/calculate-bmi",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "PATCH",
        },
    )
    assert response.status_code == 400


def run_all_tests():
    print("\n" + "=" * 50)
    print("API Edge-case Tests")
    print("=" * 50)

    test_workout_generate_plan_missing_required_field()
    print("[PASS] workout missing required field")

    test_workout_generate_plan_wrong_field_type()
    print("[PASS] workout wrong field type")

    test_user_get_not_found()
    print("[PASS] user not found")

    test_nutrition_calories_wrong_type()
    print("[PASS] nutrition wrong field type")

    test_body_calculate_bmi_missing_field()
    print("[PASS] body bmi missing field")

    test_body_fat_accepts_english_gender()
    print("[PASS] body fat english gender")

    test_nutrition_analyze_accepts_weight_alias()
    print("[PASS] nutrition analyze weight alias")

    test_cors_preflight_disallowed_method()
    print("[PASS] cors disallowed method")

    print("\n" + "=" * 50)
    print("All API Edge-case Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
