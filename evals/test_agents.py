"""Pytest entry point for agent evaluation — runs graders against eval sets.

For offline testing (no LLM calls), this validates the eval framework itself:
- Eval set loading
- Grader execution against sample responses
- Score aggregation and reporting

For live testing (with LLM), set ANTHROPIC_API_KEY and run:
  pytest evals/ -v --live
"""

import json
from pathlib import Path

import pytest

from evals.runners.eval_runner import (
    aggregate_results,
    evaluate_response,
    load_eval_sets,
)
from evals.runners.ci_reporter import check_thresholds, format_markdown_report

EVAL_DIR = Path(__file__).parent / "evalsets"


def test_eval_sets_load() -> None:
    """Verify all eval set files parse correctly."""
    cases = load_eval_sets(EVAL_DIR)
    assert len(cases) >= 30, f"Expected at least 30 eval cases, got {len(cases)}"

    categories = set(c["category"] for c in cases)
    assert "equipment" in categories
    assert "quality" in categories
    assert "production" in categories
    assert "improvement" in categories
    assert "action" in categories


def test_eval_case_structure() -> None:
    """Verify each eval case has required fields."""
    cases = load_eval_sets(EVAL_DIR)
    for case in cases:
        assert "id" in case, f"Missing 'id' in case from {case.get('source_file')}"
        assert "query" in case, f"Missing 'query' in {case['id']}"
        assert "expected_agent" in case, f"Missing 'expected_agent' in {case['id']}"
        assert "expected_tools" in case, f"Missing 'expected_tools' in {case['id']}"
        assert isinstance(case["expected_tools"], list)


def test_graders_with_sample_response() -> None:
    """Run all graders against a sample response to verify they work."""
    case = {
        "id": "TEST-001",
        "category": "equipment",
        "query": "Why is Press 1 running hot?",
        "expected_agent": "equipment_agent",
        "expected_tools": ["get_current_readings", "get_sensor_trend"],
        "ground_truth": {
            "key_facts": [
                "Temperature exceeds the normal operating range of 65C",
                "Possible causes include cooler failure or excessive cycling",
            ],
            "expected_recommendation": "Check cooler fans and reduce cycle rate",
        },
    }

    sample_response = (
        "Based on the sensor data from STP-01-PRS-HYP01, the current temperature "
        "reading is 72°C, which exceeds the maximum normal operating range of 65°C. "
        "The temperature trend shows a gradual rise over the last 4 hours. "
        "Confidence: 85%. "
        "Possible causes include cooler fan failure, high ambient temperature, "
        "or excessive cycling rate. "
        "Recommendation: 1. Immediately reduce cycle rate. 2. Inspect cooler fans. "
        "3. Check coolant flow rate."
    )

    tool_calls = [
        {"tool": "get_current_readings", "args": {"station_id": "STP-01-PRS"}, "agent": "equipment_agent"},
        {"tool": "get_sensor_trend", "args": {"machine_id": "STP-01-PRS-HYP01"}, "agent": "equipment_agent"},
    ]

    tool_outputs = [
        "STP-01-PRS-HYP01:TMP latest_value=72.3 unit=C",
        "mean=68.5 min=62.1 max=72.3 direction=rising",
    ]

    result = evaluate_response(case, sample_response, tool_calls, tool_outputs)

    assert result["case_id"] == "TEST-001"
    assert 0.0 <= result["overall_score"] <= 1.0
    assert result["scores"]["correctness"] >= 0.5
    assert result["scores"]["hallucination"] >= 0.5
    assert result["routing_correct"] is True


def test_aggregate_and_report() -> None:
    """Test that results aggregate and format correctly."""
    results = [
        {
            "case_id": "T1", "category": "equipment",
            "query": "test", "overall_score": 0.85,
            "scores": {"correctness": 0.9, "citations": 0.8, "confidence": 0.85,
                       "hallucination": 0.9, "actions": 0.7},
            "tool_coverage": 0.8, "routing_correct": True,
            "details": {},
        },
        {
            "case_id": "T2", "category": "quality",
            "query": "test", "overall_score": 0.75,
            "scores": {"correctness": 0.8, "citations": 0.7, "confidence": 0.8,
                       "hallucination": 0.85, "actions": 0.6},
            "tool_coverage": 0.7, "routing_correct": True,
            "details": {},
        },
    ]

    summary = aggregate_results(results)
    assert "equipment" in summary
    assert "quality" in summary
    assert "_overall" in summary
    assert summary["_overall"]["count"] == 2

    report = format_markdown_report(summary)
    assert "Agent Evaluation Report" in report
    assert "equipment" in report

    passed, failures = check_thresholds(summary)
    assert isinstance(passed, bool)
    assert isinstance(failures, list)
