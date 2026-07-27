"""Metric 2: Tool Parameters — rule-based checks.

Two-layer approach:
  1. If eval case has `expected_args`, exact-match each required arg value.
  2. Fallback: extract entity IDs from the query text via regex and check
     they appear somewhere in the tool call args for that tool.
"""

import re


# Patterns that identify specific entities in PrimeEV naming conventions
_ENTITY_PATTERNS = [
    (r"\b(STP|WLD|PNT|ASM|QAT)-\d{2}-[A-Z]{3}-[A-Z]{3}\d{2}\b", "machine_id"),
    (r"\b(STP|WLD|PNT|ASM|QAT)-\d{2}-[A-Z]{3}\b", "station_id"),
    (r"\bPEF-[A-Z]{2}\d{3}-\d{2}-\d{6}\b", "vin_id"),
    (r"\bSUP-[A-Z]{3}\d{2}\b", "supplier_id"),
    (r"\bLOT-[A-Z]{3}-\d{4}-\d{4}\b", "lot_number"),
    (r"\bWO-\d{4}-\d{5}\b", "wo_id"),
    (r"\bPE-(SD100|SV200|CP300)\b", "model_id"),
]


def _extract_entities_from_query(query: str) -> dict[str, list[str]]:
    """Extract all entity IDs present in the query text."""
    found: dict[str, list[str]] = {}
    for pattern, entity_type in _ENTITY_PATTERNS:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            found[entity_type] = matches
    return found


def _args_contain_value(args: dict, value: str) -> bool:
    """Check if a value appears anywhere in the args dict (substring match).

    Uses substring matching so entity IDs appearing inside search query
    strings (e.g. query="changeover PE-SD100 to PE-SV200") are found.
    """
    value_lower = value.lower()
    for v in args.values():
        if isinstance(v, str) and value_lower in v.lower():
            return True
        if isinstance(v, list) and any(
            isinstance(i, str) and value_lower in i.lower() for i in v
        ):
            return True
    return False


def grade_tool_parameters(
    query: str,
    actual_tool_calls: list[dict],
    expected_args: dict[str, dict] | None = None,
) -> dict:
    """Score whether tool parameters match the entities implied by the query.

    Args:
        query: The user's original query text.
        actual_tool_calls: List of {tool, args, agent} dicts.
        expected_args: Optional explicit mapping of tool_name → {arg: value}.
                       If provided, this takes priority over regex fallback.

    Returns:
        Dict with score, checks, mismatches.
    """
    if not actual_tool_calls:
        return {"score": 1.0, "checks": 0, "passed": 0, "mismatches": []}

    checks: list[dict] = []

    # ── Layer 1: explicit expected_args from eval case ──────────────────────
    if expected_args:
        for tool_name, required_args in expected_args.items():
            matching_calls = [tc for tc in actual_tool_calls if tc.get("tool") == tool_name]
            if not matching_calls:
                checks.append({
                    "tool": tool_name, "passed": False,
                    "reason": f"tool not called — cannot check args",
                })
                continue
            for call in matching_calls:
                call_args = call.get("args") or {}
                for arg_key, expected_val in required_args.items():
                    actual_val = call_args.get(arg_key)
                    actual_str = str(actual_val or "").lower()
                    expected_str = str(expected_val).lower()
                    # Accept exact match OR prefix match ("ASM" matches "ASM-01-PWR")
                    passed = actual_str == expected_str or actual_str.startswith(expected_str + "-")
                    checks.append({
                        "tool": tool_name,
                        "arg": arg_key,
                        "expected": expected_val,
                        "actual": actual_val,
                        "passed": passed,
                    })

    # ── Layer 2: entity regex fallback (when no expected_args given) ────────
    else:
        query_entities = _extract_entities_from_query(query)
        if query_entities:
            for tc in actual_tool_calls:
                tool_name = tc.get("tool", "")
                call_args = tc.get("args") or {}
                for entity_type, values in query_entities.items():
                    for val in values:
                        found = _args_contain_value(call_args, val)
                        checks.append({
                            "tool": tool_name,
                            "arg": entity_type,
                            "expected": val,
                            "actual": call_args.get(entity_type, "<not found>"),
                            "passed": found,
                        })

    if not checks:
        return {"score": 1.0, "checks": 0, "passed": 0,
                "mismatches": [], "note": "no entity constraints to check"}

    passed = sum(1 for c in checks if c["passed"])
    mismatches = [c for c in checks if not c["passed"]]
    score = passed / len(checks)

    return {
        "score": round(score, 3),
        "checks": len(checks),
        "passed": passed,
        "mismatches": mismatches,
    }
