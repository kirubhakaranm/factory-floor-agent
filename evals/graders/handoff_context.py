"""Metric 7: Handoff Context — state key checks.

When the root agent hands off to a sub-agent it should carry forward
specific context keys (station_id, machine_id, time_range, etc.).
Check that required keys exist and have expected values.
"""


def grade_handoff_context(
    actual_context: dict,
    expected_context_keys: list[str],
    expected_context_values: dict | None = None,
) -> dict:
    """Score handoff context completeness and correctness.

    Args:
        actual_context: The context/state dict passed to the sub-agent.
        expected_context_keys: Keys that must exist in the context.
        expected_context_values: Optional {key: value} pairs to exact-match.

    Returns:
        Dict with score, present_keys, missing_keys, wrong_values.
    """
    if not expected_context_keys and not expected_context_values:
        return {"score": 1.0, "note": "no context constraints defined"}

    checks: list[dict] = []

    # Check required keys exist
    for key in (expected_context_keys or []):
        present = key in actual_context and actual_context[key] is not None
        checks.append({"key": key, "check": "exists", "passed": present,
                       "actual": actual_context.get(key)})

    # Check specific values match
    for key, expected_val in (expected_context_values or {}).items():
        actual_val = actual_context.get(key)
        passed = str(actual_val).lower() == str(expected_val).lower()
        checks.append({"key": key, "check": "value_match",
                       "expected": expected_val, "actual": actual_val, "passed": passed})

    if not checks:
        return {"score": 1.0, "checks": 0}

    passed = sum(1 for c in checks if c["passed"])
    failures = [c for c in checks if not c["passed"]]

    return {
        "score": round(passed / len(checks), 3),
        "checks": len(checks),
        "passed": passed,
        "failures": failures,
    }
