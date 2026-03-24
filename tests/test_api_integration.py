"""
Integration Tests for FastAPI Routes
"""
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from src.main import app
from src.config import settings


client = TestClient(app)
INTERNAL_HEADERS = {"X-Internal-Token": settings.internal_api_token}


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


def test_chat_llm_config_get_and_update():
    get_resp = client.get("/api/chat/_internal/llm-config", headers=INTERNAL_HEADERS)
    assert get_resp.status_code == 200
    before = get_resp.json()
    assert "provider" in before
    assert "model" in before

    update_resp = client.put(
        "/api/chat/_internal/llm-config",
        headers=INTERNAL_HEADERS,
        json={
            "provider": "glm",
            "model": "glm-4-plus",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "",
        },
    )
    assert update_resp.status_code == 200
    after = update_resp.json()
    assert after["provider"] == "glm"
    assert after["model"] == "glm-4-plus"


def test_chat_llm_pool_get_and_update():
    get_resp = client.get("/api/chat/_internal/llm-pool", headers=INTERNAL_HEADERS)
    assert get_resp.status_code == 200
    before = get_resp.json()
    assert "active_index" in before
    assert "configs" in before
    assert "auto_fallback_enabled" in before
    assert "fallback_cooldown_seconds" in before
    assert len(before["configs"]) >= 1

    update_resp = client.put(
        "/api/chat/_internal/llm-pool",
        headers=INTERNAL_HEADERS,
        json={
            "active_index": 0,
            "auto_fallback_enabled": True,
            "fallback_cooldown_seconds": 30,
            "configs": [
                {
                    "provider": "glm",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "model": "glm-4-plus",
                    "api_key": "",
                },
                {
                    "provider": "openai",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o-mini",
                    "api_key": "",
                },
            ],
        },
    )
    assert update_resp.status_code == 200
    after = update_resp.json()
    assert after["active_index"] == 0
    assert after["auto_fallback_enabled"] is True
    assert after["fallback_cooldown_seconds"] == 30
    assert len(after["configs"]) == 2
    assert after["configs"][0]["provider"] == "glm"
    assert after["configs"][1]["provider"] == "openai"


def test_chat_llm_models_and_switch_active():
    models_resp = client.get("/api/chat/llm-models")
    assert models_resp.status_code == 200
    models_data = models_resp.json()
    assert "active_model" in models_data
    assert "models" in models_data
    assert isinstance(models_data["models"], list)
    assert len(models_data["models"]) >= 1

    target_model = models_data["models"][0]
    switch_resp = client.put("/api/chat/active-llm", json={"model": target_model})
    assert switch_resp.status_code == 200
    switch_data = switch_resp.json()
    assert switch_data["active_model"] == target_model
    assert target_model in switch_data["models"]


def test_chat_internal_endpoints_require_token():
    no_token_resp = client.get("/api/chat/_internal/llm-config")
    assert no_token_resp.status_code == 403

    wrong_token_resp = client.get(
        "/api/chat/_internal/llm-pool",
        headers={"X-Internal-Token": "wrong-token"},
    )
    assert wrong_token_resp.status_code == 403


def test_chat_active_llm_empty_model():
    response = client.put("/api/chat/active-llm", json={"model": ""})
    assert response.status_code == 400


def test_chat_active_llm_nonexistent_model():
    response = client.put("/api/chat/active-llm", json={"model": "__not_exists__"})
    assert response.status_code == 404


def test_chat_active_llm_single_model_can_switch_to_settings_pool():
    update_single_resp = client.put(
        "/api/chat/_internal/llm-config",
        headers=INTERNAL_HEADERS,
        json={
            "provider": "glm",
            "model": "glm-5",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "",
        },
    )
    assert update_single_resp.status_code == 200

    models_resp = client.get("/api/chat/llm-models")
    assert models_resp.status_code == 200
    models_data = models_resp.json()
    models = models_data.get("models", [])
    assert isinstance(models, list)
    assert len(models) >= 1

    target_model = None
    for item in models:
        if item != "glm-5":
            target_model = item
            break

    if target_model is None:
        switch_resp = client.put("/api/chat/active-llm", json={"model": "some-other-model"})
        assert switch_resp.status_code == 404
        return

    switch_resp = client.put("/api/chat/active-llm", json={"model": target_model})
    assert switch_resp.status_code == 200
    switch_data = switch_resp.json()
    assert switch_data["active_model"] == target_model


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

    test_chat_llm_config_get_and_update()
    print("[PASS] chat llm config get/update")

    test_chat_llm_pool_get_and_update()
    print("[PASS] chat llm pool get/update")

    test_chat_llm_models_and_switch_active()
    print("[PASS] chat llm models/switch active")

    test_chat_internal_endpoints_require_token()
    print("[PASS] chat internal endpoints require token")

    test_chat_active_llm_empty_model()
    print("[PASS] chat active llm empty model")

    test_chat_active_llm_nonexistent_model()
    print("[PASS] chat active llm nonexistent model")

    test_chat_active_llm_single_model_can_switch_to_settings_pool()
    print("[PASS] chat active llm single model can switch")

    print("\n" + "=" * 50)
    print("All API Integration Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
