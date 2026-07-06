"""Eval runner — orchestrates evaluation execution, collects results."""

import json
from pathlib import Path
from typing import Any


def load_eval_sets(eval_dir: Path) -> list[dict]:
    """Load all eval set JSON files from the eval directory."""
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
) -> dict:
    """Run all graders on a single eval case response.

    Args:
        case: Eval case dict with query, expected_agent, ground_truth
        response: Agent's response text
        tool_calls: List of tool calls made
        tool_outputs: List of tool output strings

    Returns:
        Dict with per-grader scores and overall score
    """
    from evals.graders.correctness import grade_correctness
    from evals.graders.citation_quality import grade_citation_quality
    from evals.graders.confidence_calibration import grade_confidence_calibration
    from evals.graders.hallucination import grade_hallucination
    from evals.graders.action_validity import grade_action_validity

    ground_truth = case.get("ground_truth", {})

    correctness = grade_correctness(response, ground_truth, tool_outputs)
    citations = grade_citation_quality(response, tool_calls, tool_outputs)
    confidence = grade_confidence_calibration(response, correctness["score"], len(tool_calls))
    hallucination = grade_hallucination(response, tool_outputs)
    actions = grade_action_validity(response, ground_truth, tool_calls)

    scores = {
        "correctness": correctness["score"],
        "citations": citations["score"],
        "confidence": confidence["score"],
        "hallucination": hallucination["score"],
        "actions": actions["score"],
    }
    overall = sum(scores.values()) / len(scores)

    # Check tool trajectory — did agent call expected tools?
    expected_tools = set(case.get("expected_tools", []))
    actual_tools = set(tc.get("tool", "") for tc in tool_calls)
    tool_coverage = len(expected_tools & actual_tools) / max(len(expected_tools), 1)

    # Check agent routing — was query sent to expected agent?
    expected_agent = case.get("expected_agent", "")
    actual_agents = set(tc.get("agent", "") for tc in tool_calls)
    routing_correct = expected_agent in actual_agents or not expected_agent

    return {
        "case_id": case.get("id", "unknown"),
        "category": case.get("category", "unknown"),
        "query": case.get("query", ""),
        "scores": scores,
        "overall_score": round(overall, 3),
        "tool_coverage": round(tool_coverage, 3),
        "routing_correct": routing_correct,
        "details": {
            "correctness": correctness,
            "citations": citations,
            "confidence": confidence,
            "hallucination": hallucination,
            "actions": actions,
        },
    }


def aggregate_results(results: list[dict]) -> dict:
    """Aggregate eval results by category and overall."""
    from collections import defaultdict

    by_category: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_category[r["category"]].append(r)

    summary = {}
    for category, cat_results in by_category.items():
        n = len(cat_results)
        summary[category] = {
            "count": n,
            "avg_overall": round(sum(r["overall_score"] for r in cat_results) / n, 3),
            "avg_correctness": round(sum(r["scores"]["correctness"] for r in cat_results) / n, 3),
            "avg_citations": round(sum(r["scores"]["citations"] for r in cat_results) / n, 3),
            "avg_confidence": round(sum(r["scores"]["confidence"] for r in cat_results) / n, 3),
            "avg_hallucination": round(sum(r["scores"]["hallucination"] for r in cat_results) / n, 3),
            "avg_actions": round(sum(r["scores"]["actions"] for r in cat_results) / n, 3),
            "avg_tool_coverage": round(sum(r["tool_coverage"] for r in cat_results) / n, 3),
            "routing_accuracy": round(sum(1 for r in cat_results if r["routing_correct"]) / n, 3),
        }

    all_results = results
    n_total = len(all_results)
    summary["_overall"] = {
        "count": n_total,
        "avg_overall": round(sum(r["overall_score"] for r in all_results) / max(n_total, 1), 3),
        "avg_tool_coverage": round(sum(r["tool_coverage"] for r in all_results) / max(n_total, 1), 3),
        "routing_accuracy": round(sum(1 for r in all_results if r["routing_correct"]) / max(n_total, 1), 3),
    }

    return summary
