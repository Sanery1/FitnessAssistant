"""
Performance Baseline Tests for FastAPI Routes
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def _request_health() -> float:
    start = time.perf_counter()
    response = client.get("/health")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert response.status_code == 200
    return elapsed_ms


def _request_bmi() -> float:
    start = time.perf_counter()
    response = client.post(
        "/api/body/calculate-bmi",
        json={"height": 175, "weight": 70},
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert response.status_code == 200
    return elapsed_ms


def test_health_latency_baseline():
    samples = [_request_health() for _ in range(20)]
    avg = sum(samples) / len(samples)
    p95 = sorted(samples)[int(len(samples) * 0.95) - 1]

    # Conservative threshold for local baseline testing.
    assert avg < 100.0
    assert p95 < 200.0


def test_bmi_latency_baseline():
    samples = [_request_bmi() for _ in range(20)]
    avg = sum(samples) / len(samples)
    p95 = sorted(samples)[int(len(samples) * 0.95) - 1]

    # Conservative threshold for local baseline testing.
    assert avg < 200.0
    assert p95 < 400.0


def test_bmi_concurrent_error_rate():
    total = 40
    workers = 8
    errors = 0
    durations = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_request_bmi) for _ in range(total)]
        for future in as_completed(futures):
            try:
                durations.append(future.result())
            except Exception:
                errors += 1

    error_rate = errors / total
    avg = sum(durations) / len(durations) if durations else 9999

    assert error_rate == 0.0
    assert avg < 300.0


def run_all_tests():
    print("\n" + "=" * 50)
    print("Performance Baseline Tests")
    print("=" * 50)

    test_health_latency_baseline()
    print("[PASS] health latency baseline")

    test_bmi_latency_baseline()
    print("[PASS] bmi latency baseline")

    test_bmi_concurrent_error_rate()
    print("[PASS] bmi concurrent error rate")

    print("\n" + "=" * 50)
    print("All Performance Baseline Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
