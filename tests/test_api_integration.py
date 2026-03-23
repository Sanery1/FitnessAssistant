"""
Integration Tests for FastAPI Routes
"""
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from src.main import app
from src.config import settings


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.version


def test_generate_workout_plan():
    response = client.post(
        "/api/workout/generate-plan",
        json={
            "goal": "减脂",
            "level": "初学者",
            "days_per_week": 3,
            "minutes_per_day": 45
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "sessions" in data
    assert len(data["sessions"]) == 3


def test_calculate_calories():
    response = client.post(
        "/api/nutrition/calculate-calories",
        json={
            "gender": "男",
            "age": 25,
            "height": 175,
            "weight": 70,
            "activity_level": "中度活动",
            "goal": "减脂"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "target_calories" in data
    assert "macros" in data


def test_calculate_bmi():
    response = client.post(
        "/api/body/calculate-bmi",
        json={"height": 175, "weight": 70},
    )
    assert response.status_code == 200
    data = response.json()
    assert "bmi" in data
    assert "category" in data


def test_cors_allowed_origin_preflight():
    allowed_origin = settings.cors_origins[0]
    response = client.options(
        "/api/body/calculate-bmi",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin


def test_cors_disallowed_origin_preflight():
    response = client.options(
        "/api/body/calculate-bmi",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400


def run_all_tests():
    print("\n" + "=" * 50)
    print("API Integration Tests")
    print("=" * 50)

    test_health_check()
    print("[PASS] health check")

    test_generate_workout_plan()
    print("[PASS] workout generate plan")

    test_calculate_calories()
    print("[PASS] nutrition calculate calories")

    test_calculate_bmi()
    print("[PASS] body calculate bmi")

    test_cors_allowed_origin_preflight()
    print("[PASS] cors allowed origin")

    test_cors_disallowed_origin_preflight()
    print("[PASS] cors disallowed origin")

    print("\n" + "=" * 50)
    print("All API Integration Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
