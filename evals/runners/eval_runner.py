"""Eval runner — orchestrates all 10 metrics across two tiers.

Tier 1 (always, free):
  tool_selection, tool_parameters, routing_accuracy, trajectory, safety
  correctness (numeric part only)

Tier 2 (--llm-judge flag, costs tokens):
  faithfulness, relevance, multi_turn_coherence
  correctness (LLM part for explanations)
"""

import json
from pathlib import Path


def load_eval_sets(eval_dir: Path) -> list[dict]:
    """Load all eval set JSON files, tagging each case with its category."""
    all_cases: list[dict] = []
    for json_file in sorted(eval_dir.rglob("*.json")):
        with open(json_file) as f:
            cases = json.load(f)
        category = json_file.parent.name
        for case in cases:
            case["category"] = category
            case["source_file"] = json_file.name
        all_cases.extend(cases)
    return all_cases


def evaluate_response(
    case: dict,
    response: str,
    tool_calls: list[dict],
    tool_outputs: list[str],
    use_llm: bool = False,
    agent_context: dict | None = None,
) -> dict:
    """Run all applicable metrics on a single eval case response.

    Args:
        case: Eval case dict (query, expected_tools, expected_trajectory, etc.)
        response: Agent's final response text.
        tool_calls: List of {tool, args, agent} dicts made during the run.
        tool_outputs: Raw tool output strings.
        use_llm: Enable Tier 2 LLM judge metrics (faithfulness, relevance, coherence).
        agent_context: State dict passed between agents (for handoff_context check).

    Returns:
        Dict with per-metric scores, overall, and tier metadata.
    """
    from evals.graders.tool_selection import grade_tool_selection
    from evals.graders.tool_parameters import grade_tool_parameters
    from evals.graders.faithfulness import grade_faithfulness
    from evals.graders.correctness import grade_correctness
    from evals.graders.relevance import grade_relevance
    from evals.graders.routing_accuracy import grade_routing_accuracy
    from evals.graders.handoff_context import grade_handoff_context
    from evals.graders.trajectory import grade_trajectory
    from evals.graders.multi_turn_coherence import grade_multi_turn_coherence
    from evals.graders.safety import grade_safety
    from evals.graders.clarification import grade_clarification

    query = case.get("query", "")
    ground_truth = case.get("ground_truth", {})

    # ── Tier 1: always run ──────────────────────────────────────────────────

    # Only grade tool selection when case explicitly defines expected_tools.
    # RT cases omit the key entirely — don't penalize them for calling tools.
    if "expected_tools" in case:
        tool_sel = grade_tool_selection(
            expected_tools=case["expected_tools"],
            actual_tool_calls=tool_calls,
        )
    else:
        tool_sel = {"score": 1.0, "note": "no expected_tools defined — routing-only case"}

    tool_params = grade_tool_parameters(
        query=query,
        actual_tool_calls=tool_calls,
        expected_args=case.get("expected_args"),
    )

    routing = grade_routing_accuracy(
        expected_agent=case.get("expected_agent", ""),
        actual_tool_calls=tool_calls,
        wrong_agents=case.get("wrong_agents"),
        agents_invoked=set(agent_context.get("agents_invoked", [])) if agent_context else None,
    )

    trajectory = grade_trajectory(
        expected_trajectory=case.get("expected_trajectory", []),
        actual_tool_calls=tool_calls,
    )

    safety = grade_safety(
        query=query,
        response=response,
        safety_constraints=case.get("safety_constraints"),
    )

    correctness = grade_correctness(
        response=response,
        ground_truth=ground_truth,
        tool_outputs=tool_outputs,
        use_llm=use_llm,
    )

    # Clarification (only meaningful for CL-* cases)
    clarification = grade_clarification(
        response=response,
        required_clarifications=case.get("required_clarifications", []),
    )

    # Handoff context (only meaningful when agent_context provided)
    handoff = grade_handoff_context(
        actual_context=agent_context or {},
        expected_context_keys=case.get("expected_context_keys", []),
        expected_context_values=case.get("expected_context_values"),
    )

    # ── Tier 2: LLM judge (skipped if use_llm=False) ────────────────────────

    faithfulness = grade_faithfulness(
        response=response,
        tool_outputs=tool_outputs,
        use_llm=use_llm,
        query=query,
    )

    relevance = grade_relevance(
        query=query,
        response=response,
        use_llm=use_llm,
    )

    coherence = grade_multi_turn_coherence(
        response=response,
        conversation_history=case.get("conversation_history"),
        use_llm=use_llm,
    )

    # ── Score aggregation ───────────────────────────────────────────────────

    # Tier 1 scores (always count)
    tier1_scores = {
        "tool_selection": tool_sel["score"],
        "tool_parameters": tool_params["score"],
        "routing_accuracy": routing["score"],
        "trajectory": trajectory["score"],
        "safety": safety["score"],
        "correctness": correctness["score"],
    }
    # Include handoff only if constraints were defined
    if case.get("expected_context_keys") or case.get("expected_context_values"):
        tier1_scores["handoff_context"] = handoff["score"]

    # Include clarification only for cases that define required_clarifications
    if case.get("required_clarifications"):
        tier1_scores["clarification"] = clarification["score"]

    # Tier 2 scores (only count when use_llm=True)
    tier2_scores = {}
    if use_llm:
        tier2_scores["faithfulness"] = faithfulness["score"]
        tier2_scores["relevance"] = relevance["score"]
        if case.get("conversation_history"):
            tier2_scores["multi_turn_coherence"] = coherence["score"]

    all_scores = {**tier1_scores, **tier2_scores}
    overall = sum(all_scores.values()) / len(all_scores) if all_scores else 0.0

    # Sub-scores: visible in the result JSON for debugging but NOT counted in
    # overall (they're already captured inside trajectory["score"]).
    trajectory_sub = {
        "trajectory_coverage": trajectory.get("trajectory_coverage"),
        "trajectory_order": trajectory.get("trajectory_order"),
    }

    return {
        "case_id": case.get("id", "unknown"),
        "category": case.get("category", "unknown"),
        "query": query,
        "overall_score": round(overall, 3),
        "tier": "full" if use_llm else "fast",
        "scores": {**all_scores, **{k: v for k, v in trajectory_sub.items() if v is not None}},
        "details": {
            "tool_selection": tool_sel,
            "tool_parameters": tool_params,
            "routing_accuracy": routing,
            "trajectory": trajectory,
            "safety": safety,
            "correctness": correctness,
            "handoff_context": handoff,
            "clarification": clarification,
            "faithfulness": faithfulness,
            "relevance": relevance,
            "multi_turn_coherence": coherence,
        },
    }


def aggregate_results(results: list[dict]) -> dict:
    """Aggregate eval results by category and overall."""
    from collections import defaultdict

    by_category: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_category[r["category"]].append(r)

    def _avg(items: list[dict], key: str) -> float:
        """Average a named score key across a list of result dicts, ignoring None."""
        vals = [r["scores"].get(key) for r in items if r["scores"].get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    summary = {}
    for category, cat_results in by_category.items():
        n = len(cat_results)
        summary[category] = {
            "count": n,
            "avg_overall": round(sum(r["overall_score"] for r in cat_results) / n, 3),
            "avg_tool_selection": _avg(cat_results, "tool_selection"),
            "avg_tool_parameters": _avg(cat_results, "tool_parameters"),
            "avg_routing_accuracy": _avg(cat_results, "routing_accuracy"),
            "avg_trajectory": _avg(cat_results, "trajectory"),
            "avg_trajectory_coverage": _avg(cat_results, "trajectory_coverage"),
            "avg_trajectory_order": _avg(cat_results, "trajectory_order"),
            "avg_safety": _avg(cat_results, "safety"),
            "avg_correctness": _avg(cat_results, "correctness"),
            "avg_faithfulness": _avg(cat_results, "faithfulness"),
            "avg_relevance": _avg(cat_results, "relevance"),
        }

    all_n = len(results)
    summary["_overall"] = {
        "count": all_n,
        "avg_overall": round(sum(r["overall_score"] for r in results) / max(all_n, 1), 3),
        "avg_tool_selection": _avg(results, "tool_selection"),
        "avg_routing_accuracy": _avg(results, "routing_accuracy"),
        "avg_trajectory": _avg(results, "trajectory"),
        "avg_trajectory_coverage": _avg(results, "trajectory_coverage"),
        "avg_trajectory_order": _avg(results, "trajectory_order"),
        "avg_safety": _avg(results, "safety"),
        "avg_faithfulness": _avg(results, "faithfulness"),
        "avg_relevance": _avg(results, "relevance"),
    }

    return summary
