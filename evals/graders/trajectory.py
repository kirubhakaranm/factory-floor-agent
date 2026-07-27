"""Metric 8: Trajectory — sequence comparison.

Compare the ordered list of tool calls the agent made against the expected
sequence. Scores both step coverage (did it call the right tools?) and
order correctness (did it call them in a sensible order?).
"""


def grade_trajectory(
    expected_trajectory: list[dict],
    actual_tool_calls: list[dict],
) -> dict:
    """Score agent trajectory against the expected tool call sequence.

    Expected trajectory format:
        [{"tool": "get_failure_history", "required_args": {"machine_id": "STP-01-PRS-HYP01"}},
         {"tool": "get_mtbf_mttr",       "required_args": {}},
         {"tool": "search_past_issues",  "required_args": {}}]

    required_args: only the args that MUST match (others are ignored).
    Empty required_args means "tool must be called, args unconstrained".

    Args:
        expected_trajectory: Ordered list of expected steps.
        actual_tool_calls: Ordered list of {tool, args, agent} dicts from the run.

    Returns:
        Dict with score, step_coverage, order_score, step_results.
    """
    if not expected_trajectory:
        return {"score": 1.0, "note": "no expected_trajectory defined"}

    actual_tools_ordered = [tc.get("tool", "") for tc in actual_tool_calls]
    actual_args_by_tool: dict[str, list[dict]] = {}
    for tc in actual_tool_calls:
        t = tc.get("tool", "")
        actual_args_by_tool.setdefault(t, []).append(tc.get("args") or {})

    step_results = []

    for step in expected_trajectory:
        tool = step["tool"]
        required_args = step.get("required_args", {})

        # Was the tool called at all?
        called = tool in actual_args_by_tool
        if not called:
            step_results.append({"tool": tool, "called": False, "args_ok": False, "passed": False})
            continue

        # Check required args on any matching call
        args_ok = True
        if required_args:
            args_ok = False
            for call_args in actual_args_by_tool[tool]:
                if all(
                    str(call_args.get(k, "")).lower() == str(v).lower()
                    for k, v in required_args.items()
                ):
                    args_ok = True
                    break

        step_results.append({
            "tool": tool,
            "called": True,
            "args_ok": args_ok,
            "passed": args_ok,
            "required_args": required_args,
        })

    # ── Sub-score 1: Coverage — did the agent call all expected tools? ─────────
    passed_steps = sum(1 for s in step_results if s["passed"])
    coverage = passed_steps / len(expected_trajectory)

    # ── Sub-score 2: Order — did the called tools appear in the right sequence? ─
    expected_order = [s["tool"] for s in expected_trajectory]
    actual_filtered = [t for t in actual_tools_ordered if t in set(expected_order)]
    order = _subsequence_score(expected_order, actual_filtered)

    # Combined score: 70% coverage + 30% order (coverage matters more —
    # calling the wrong tools in the right order is worse than calling the
    # right tools slightly out of order)
    combined = 0.7 * coverage + 0.3 * order

    return {
        "score": round(combined, 3),
        # Sub-scores visible for debugging
        "trajectory_coverage": round(coverage, 3),  # were all expected tools called?
        "trajectory_order": round(order, 3),         # were they called in the right order?
        "steps_passed": passed_steps,
        "steps_total": len(expected_trajectory),
        "step_results": step_results,
    }


def _subsequence_score(expected: list[str], actual: list[str]) -> float:
    """Score how well actual preserves the relative order of expected items.

    Uses longest common subsequence length / len(expected).
    """
    if not expected or not actual:
        return 1.0 if not expected else 0.0

    # LCS via DP
    m, n = len(expected), len(actual)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if expected[i - 1] == actual[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n] / len(expected)
