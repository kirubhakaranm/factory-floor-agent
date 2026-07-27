"""Metric 1: Tool Selection — exact match.

Binary per tool: right tool called or not. Reports precision, recall, F1.
No heuristics — a tool either appeared in tool_calls or it didn't.
"""


def grade_tool_selection(
    expected_tools: list[str],
    actual_tool_calls: list[dict],
) -> dict:
    """Score tool selection via exact set comparison.

    Args:
        expected_tools: Tool names the agent should have called.
        actual_tool_calls: List of {tool, args, agent} dicts from the run.

    Returns:
        Dict with precision, recall, f1, score, missing_tools, extra_tools.
    """
    expected = set(expected_tools)
    actual = set(tc.get("tool", "") for tc in actual_tool_calls)

    if not expected:
        # Refusal/clarification cases — agent must NOT call any tools
        if actual:
            return {
                "score": 0.0, "precision": 0.0, "recall": 1.0, "f1": 0.0,
                "missing_tools": [], "extra_tools": sorted(actual),
                "note": "no tools expected (refusal/clarification case) but tools were called",
            }
        return {"score": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0,
                "missing_tools": [], "extra_tools": []}

    tp = expected & actual
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    precision = len(tp) / len(actual) if actual else 0.0
    recall = len(tp) / len(expected)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "score": round(f1, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "expected": sorted(expected),
        "actual": sorted(actual),
        "missing_tools": missing,
        "extra_tools": extra,
    }
