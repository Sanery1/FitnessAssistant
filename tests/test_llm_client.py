"""
Tests for LLM Client Utilities
"""
import sys
sys.path.insert(0, ".")

from src.services.llm_client import normalize_tool_arguments


def test_normalize_tool_arguments_from_dict():
    args = {"height": 175, "weight": 70}
    normalized = normalize_tool_arguments(args)
    assert normalized == args


def test_normalize_tool_arguments_from_json_string():
    normalized = normalize_tool_arguments('{"goal": "增肌", "days": 4}')
    assert normalized["goal"] == "增肌"
    assert normalized["days"] == 4


def test_normalize_tool_arguments_invalid_json():
    try:
        normalize_tool_arguments('{"goal": "增肌"')
        assert False, "Expected ValueError for invalid JSON"
    except ValueError as exc:
        assert "JSON 解析失败" in str(exc)


def test_normalize_tool_arguments_non_object_json():
    try:
        normalize_tool_arguments('[1, 2, 3]')
        assert False, "Expected ValueError for non-object JSON"
    except ValueError as exc:
        assert "JSON 对象" in str(exc)


def run_all_tests():
    print("\n" + "=" * 50)
    print("LLM Client Utility Tests")
    print("=" * 50)

    test_normalize_tool_arguments_from_dict()
    print("[PASS] normalize from dict")

    test_normalize_tool_arguments_from_json_string()
    print("[PASS] normalize from json string")

    test_normalize_tool_arguments_invalid_json()
    print("[PASS] invalid json handling")

    test_normalize_tool_arguments_non_object_json()
    print("[PASS] non-object json handling")

    print("\n" + "=" * 50)
    print("All LLM Utility Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
