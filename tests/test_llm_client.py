"""
Tests for LLM Client Utilities
"""
import sys
sys.path.insert(0, ".")

from src.services.llm_client import normalize_tool_arguments, extract_compat_tool_calls


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


def test_extract_compat_tool_calls_from_minimax_markup():
    content = """
你好，我先计算一下。
<minimax:tool_call>
<invoke name="calculate_bmi">
<parameter name="weight">82</parameter>
<parameter name="height">178</parameter>
</invoke>
</minimax:tool_call>
"""
    parsed = extract_compat_tool_calls(content)
    assert len(parsed["tool_calls"]) == 1
    assert parsed["tool_calls"][0]["name"] == "calculate_bmi"
    assert parsed["tool_calls"][0]["arguments"]["weight"] == 82
    assert parsed["tool_calls"][0]["arguments"]["height"] == 178
    assert "<minimax:tool_call>" not in parsed["content"]


def test_extract_compat_tool_calls_when_no_markup():
    content = "普通文本"
    parsed = extract_compat_tool_calls(content)
    assert parsed["tool_calls"] == []
    assert parsed["content"] == "普通文本"


def test_extract_compat_tool_calls_from_tool_code_markup():
    content = """
你好，我来计算。
<tool_code>
{
    tool => 'calculate_bmi',
    args => '\n<weight>82</weight>\n<height>178</height>\n'
}
</tool_code>
"""
    parsed = extract_compat_tool_calls(content)
    assert len(parsed["tool_calls"]) == 1
    assert parsed["tool_calls"][0]["name"] == "calculate_bmi"
    assert parsed["tool_calls"][0]["arguments"]["weight"] == 82
    assert parsed["tool_calls"][0]["arguments"]["height"] == 178
    assert "<tool_code>" not in parsed["content"]


def test_extract_compat_tool_calls_from_tool_block_markup():
    content = """
我先处理一下。
<tool_call>
<tool name="calculate_bmi">
<param name="weight">82</param>
<param name="height">178</param>
</tool>
</tool_call>
"""
    parsed = extract_compat_tool_calls(content)
    assert len(parsed["tool_calls"]) == 1
    assert parsed["tool_calls"][0]["name"] == "calculate_bmi"
    assert parsed["tool_calls"][0]["arguments"]["weight"] == 82
    assert parsed["tool_calls"][0]["arguments"]["height"] == 178
    assert "<tool_call>" not in parsed["content"]


def test_extract_compat_tool_calls_from_function_call_markup():
    content = """
你好！让我先帮你计算一下。
<FunctionCall>
struct Tool {
tool: "calculate_bmi",
args: {
weight=82
height=178
}
}
</FunctionCall>
"""
    parsed = extract_compat_tool_calls(content)
    assert len(parsed["tool_calls"]) == 1
    assert parsed["tool_calls"][0]["name"] == "calculate_bmi"
    assert parsed["tool_calls"][0]["arguments"]["weight"] == 82
    assert parsed["tool_calls"][0]["arguments"]["height"] == 178
    assert "<FunctionCall>" not in parsed["content"]


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

    test_extract_compat_tool_calls_from_minimax_markup()
    print("[PASS] parse minimax compat tool_call")

    test_extract_compat_tool_calls_when_no_markup()
    print("[PASS] no compat tool_call passthrough")

    test_extract_compat_tool_calls_from_tool_code_markup()
    print("[PASS] parse tool_code compat tool_call")

    test_extract_compat_tool_calls_from_tool_block_markup()
    print("[PASS] parse tool block compat tool_call")

    test_extract_compat_tool_calls_from_function_call_markup()
    print("[PASS] parse FunctionCall compat tool_call")

    print("\n" + "=" * 50)
    print("All LLM Utility Tests Passed!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
