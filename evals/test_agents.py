"""Pytest entry point for agent evaluation.

Tier 1 (default): deterministic graders only — no API calls, runs in seconds.
Tier 2 (--llm-judge): also runs faithfulness, relevance, multi-turn coherence.
Tier 3 (--live): actually calls the agent; requires ANTHROPIC_API_KEY.

Usage:
  pytest evals/ -v                          # Tier 1 only
  pytest evals/ -v --llm-judge              # Tier 1 + 2
  pytest evals/ -v --live                   # Tier 1 + 3 (live agent)
  pytest evals/ -v --live --llm-judge       # All tiers
"""

import asyncio
import os
import time
import uuid
from pathlib import Path

import pytest
import google.genai.types as genai_types

from evals.runners.eval_runner import aggregate_results, evaluate_response, load_eval_sets
from evals.runners.ci_reporter import check_thresholds, format_markdown_report
from evals.conftest import write_result

EVAL_DIR = Path(__file__).parent / "evalsets"
SCORE_THRESHOLD = 0.60       # minimum overall score per case to pass
APP_NAME = "primeev_factory_agent"


# ── Live agent runner ────────────────────────────────────────────────────────

async def _run_case_async(
    case: dict, runner, session_service
) -> tuple[str, list[dict], list[str], dict, list[dict]]:
    """Run one eval case through the live agent and collect outputs + ADK trace.

    For multi-turn cases (conversation_history present), the prior turns are
    sent through the agent first so the session has genuine history, then only
    the final query turn is scored.

    Returns:
        response      — agent's final text response to the eval query
        tool_calls    — list of {tool, args, agent} from the scored turn
        tool_outputs  — list of tool response strings from the scored turn
        agent_context — dict built from tool args (for handoff_context grader)
        trace         — full ordered ADK event sequence with timestamps
    """
    user_id = "eval_runner"
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    def _make_message(text: str) -> genai_types.Content:
        """Wrap a plain text string in a user-role ADK Content object."""
        return genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=text)],
        )

    # ── Replay prior conversation turns (not scored) ─────────────────────────
    for turn in case.get("conversation_history", []):
        if turn["role"] == "user":
            async for _ in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=_make_message(turn["content"]),
            ):
                pass  # advance session state, discard events

    # ── Run the eval query (scored turn) ─────────────────────────────────────
    tool_calls: list[dict] = []
    tool_outputs: list[str] = []
    agents_invoked: set[str] = set()
    final_response = ""
    trace: list[dict] = []
    seq = 0
    run_start = time.time()

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=_make_message(case["query"]),
    ):
        # ADK events expose .timestamp on some versions; fall back to wall clock
        ts = round(getattr(event, "timestamp", time.time()) - run_start, 3)
        author = event.author or ""
        if author and author != "user":
            agents_invoked.add(author)

        # ── Tool calls ───────────────────────────────────────────────────────
        for fc in (event.get_function_calls() or []):
            args = dict(fc.args) if fc.args else {}
            if fc.name == "transfer_to_agent":
                target = (
                    args.get("agent_name")
                    or args.get("agent")
                    or next((v for v in args.values() if isinstance(v, str)), "")
                )
                if target:
                    agents_invoked.add(target)
                trace.append({
                    "seq": seq, "ts": ts, "author": author,
                    "type": "route", "target": target,
                })
                seq += 1
                continue

            trace.append({
                "seq": seq, "ts": ts, "author": author,
                "type": "tool_call", "tool": fc.name, "args": args,
            })
            seq += 1
            tool_calls.append({"tool": fc.name, "args": args, "agent": author})

        # ── Tool responses ───────────────────────────────────────────────────
        for fr in (event.get_function_responses() or []):
            resp = fr.response
            output = str(resp.get("result", resp)) if isinstance(resp, dict) else str(resp)
            trace.append({
                "seq": seq, "ts": ts, "author": author,
                "type": "tool_response", "tool": fr.name,
                # cap stored output at 1000 chars to keep files manageable
                "output": output[:1000],
                "truncated": len(output) > 1000,
            })
            seq += 1
            tool_outputs.append(output)

        # ── Agent text (intermediate reasoning or final response) ────────────
        if event.content and event.content.parts:
            is_final = event.is_final_response()
            for part in event.content.parts:
                if not part.text:
                    continue
                trace.append({
                    "seq": seq, "ts": ts, "author": author,
                    "type": "final_response" if is_final else "agent_text",
                    "text": part.text[:2000],
                    "truncated": len(part.text) > 2000,
                })
                seq += 1
                if is_final:
                    final_response += part.text

    trace.append({"seq": seq, "type": "run_end", "elapsed_s": round(time.time() - run_start, 3)})

    # Build agent_context from all tool args (for handoff_context grader)
    agent_context: dict = {"agents_invoked": sorted(agents_invoked)}
    for tc in tool_calls:
        agent_context.update(tc["args"])

    return final_response, tool_calls, tool_outputs, agent_context, trace


# ── Parametrized live eval test ──────────────────────────────────────────────

@pytest.mark.parametrize("case", load_eval_sets(EVAL_DIR), ids=lambda c: c["id"])
def test_live_eval(case: dict, request: pytest.FixtureRequest) -> None:
    """Run a single eval case through the live agent and assert the overall score passes."""
    if not request.config.getoption("--live"):
        pytest.skip("pass --live to run against the real agent")

    from google.adk.runners import Runner as AdkRunner
    from google.adk.sessions import InMemorySessionService
    from src.agents.agent import root_agent

    session_service = InMemorySessionService()
    runner = AdkRunner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    use_llm = request.config.getoption("--llm-judge")

    try:
        response, tool_calls, tool_outputs, agent_context, trace = asyncio.run(
            _run_case_async(case, runner, session_service)
        )
    except Exception as _exc:
        _err = str(_exc)
        _crash_result = {
            "case_id": case.get("id", "unknown"),
            "category": case.get("category", "unknown"),
            "query": case.get("query", ""),
            "overall_score": 0.0,
            "tier": "fast",
            "scores": {"routing_accuracy": 0.0},
            "details": {},
            "error": f"crash:{type(_exc).__name__}: {_err[:300]}",
            "trace": [],
            "model": os.environ.get("AGENT_MODEL", "anthropic/claude-haiku-4-5"),
        }
        write_result(_crash_result)
        pytest.fail(f"[{case['id']}] CRASH ({type(_exc).__name__}): {_err[:200]}")

    result = evaluate_response(
        case=case,
        response=response,
        tool_calls=tool_calls,
        tool_outputs=tool_outputs,
        use_llm=use_llm,
        agent_context=agent_context,
    )

    # Attach ADK trace to result for post-run analysis
    result["trace"] = trace
    result["model"] = os.environ.get("AGENT_MODEL", "anthropic/claude-haiku-4-5")

    # Write result file (xdist-safe — one file per case, no shared state)
    write_result(result)

    score_line = " | ".join(f"{k}={v:.2f}" for k, v in result["scores"].items())
    print(f"\n[{case['id']}] overall={result['overall_score']:.3f} | {score_line}")
    if not response:
        print("  WARNING: empty response from agent")

    assert result["overall_score"] >= SCORE_THRESHOLD, (
        f"[{case['id']}] overall={result['overall_score']:.3f} < {SCORE_THRESHOLD}\n"
        f"Scores: {result['scores']}\n"
        f"Tools called: {[t['tool'] for t in tool_calls]}\n"
        f"Response (first 400 chars): {response[:400]}"
    )


# ── Framework tests (always run) ────────────────────────────────────────────

def test_eval_sets_load() -> None:
    """Eval set JSON files must load at least 30 cases covering all 5 required categories."""
    cases = load_eval_sets(EVAL_DIR)
    assert len(cases) >= 30, f"Expected >= 30 eval cases, got {len(cases)}"
    categories = {c["category"] for c in cases}
    for cat in ("equipment", "quality", "production", "improvement", "action"):
        assert cat in categories, f"Missing category: {cat}"


def test_eval_case_structure() -> None:
    """Every eval case must have required fields: id, query, expected_agent, expected_tools."""
    cases = load_eval_sets(EVAL_DIR)
    for case in cases:
        assert "id" in case
        assert "query" in case
        assert "expected_agent" in case
        assert isinstance(case.get("expected_tools", []), list)


def test_all_10_graders_import():
    """Verify all graders import without errors."""
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
    assert all([grade_tool_selection, grade_tool_parameters, grade_faithfulness,
                grade_correctness, grade_relevance, grade_routing_accuracy,
                grade_handoff_context, grade_trajectory, grade_multi_turn_coherence,
                grade_safety])


def test_evaluate_response_full_case():
    """Run all Tier 1 graders on a fully-specified sample case."""
    case = {
        "id": "TEST-001",
        "category": "equipment",
        "query": "Press 1 hydraulic oil temperature is reading 72°C. Is this a problem?",
        "expected_agent": "equipment_agent",
        "expected_tools": ["get_current_readings", "get_sensor_trend"],
        "expected_trajectory": [
            {"tool": "get_current_readings", "required_args": {"station_id": "STP-01-PRS"}},
            {"tool": "get_sensor_trend",     "required_args": {"machine_id": "STP-01-PRS-HYP01"}},
        ],
        "expected_args": {
            "get_current_readings": {"station_id": "STP-01-PRS"},
            "get_sensor_trend":     {"machine_id": "STP-01-PRS-HYP01"},
        },
        "ground_truth": {
            "key_facts": [
                "72°C exceeds the max normal operating range of 65°C",
                "Normal operating range is 35-65°C",
            ],
            "expected_recommendation": "Reduce cycle rate, check cooler fans",
        },
    }

    response = (
        "The current temperature at STP-01-PRS-HYP01 is 72°C, which exceeds the "
        "normal operating range of 35-65°C. This is above the safe maximum of 65°C. "
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

    result = evaluate_response(case, response, tool_calls, tool_outputs, use_llm=False)

    assert result["case_id"] == "TEST-001"
    assert 0.0 <= result["overall_score"] <= 1.0
    assert result["scores"]["tool_selection"] == 1.0          # exact match: both tools called
    assert result["scores"]["routing_accuracy"] == 1.0        # equipment_agent used
    assert result["scores"]["tool_parameters"] >= 0.8         # STP-01-PRS / HYP01 matched
    assert result["scores"]["trajectory"] >= 0.7              # correct order
    assert result["scores"]["safety"] == 1.0                  # no violations
    assert result["scores"]["correctness"] >= 0.5


def test_trajectory_order_matters():
    """Verify trajectory grader penalises wrong call order."""
    from evals.graders.trajectory import grade_trajectory

    expected = [
        {"tool": "get_failure_history", "required_args": {}},
        {"tool": "get_mtbf_mttr",       "required_args": {}},
        {"tool": "search_past_issues",  "required_args": {}},
    ]

    # Correct order
    correct_calls = [
        {"tool": "get_failure_history", "args": {}, "agent": "equipment_agent"},
        {"tool": "get_mtbf_mttr",       "args": {}, "agent": "equipment_agent"},
        {"tool": "search_past_issues",  "args": {}, "agent": "equipment_agent"},
    ]
    good = grade_trajectory(expected, correct_calls)

    # Reversed order
    reversed_calls = list(reversed(correct_calls))
    bad = grade_trajectory(expected, reversed_calls)

    assert good["score"] > bad["score"], "Correct order should score higher than reversed"
    assert good["trajectory_coverage"] == bad["trajectory_coverage"] == 1.0  # both call all tools


def test_safety_catches_violations() -> None:
    """Safety grader must flag destructive shell commands and pass benign responses."""
    from evals.graders.safety import grade_safety
    safe = grade_safety("what's the temp?", "The temperature is 72°C.")
    assert safe["safe"] is True
    assert safe["score"] == 1.0

    unsafe = grade_safety("what's the temp?", "Run: rm -rf /var/data to clear logs")
    assert unsafe["safe"] is False
    assert unsafe["score"] < 1.0


def test_aggregate_and_report() -> None:
    """aggregate_results and format_markdown_report produce valid summaries and pass threshold check."""
    results = [
        {
            "case_id": "T1", "category": "equipment", "query": "test",
            "overall_score": 0.85, "tier": "fast",
            "scores": {"tool_selection": 1.0, "tool_parameters": 0.8,
                       "routing_accuracy": 1.0, "trajectory": 0.8,
                       "safety": 1.0, "correctness": 0.7},
            "details": {},
        },
        {
            "case_id": "T2", "category": "quality", "query": "test",
            "overall_score": 0.75, "tier": "fast",
            "scores": {"tool_selection": 0.75, "tool_parameters": 0.6,
                       "routing_accuracy": 1.0, "trajectory": 0.65,
                       "safety": 1.0, "correctness": 0.6},
            "details": {},
        },
    ]

    summary = aggregate_results(results)
    assert "equipment" in summary
    assert "quality" in summary
    assert "_overall" in summary

    report = format_markdown_report(summary)
    assert "Agent Evaluation Report" in report
    assert "Tool Sel" in report

    passed, failures = check_thresholds(summary, llm_judge_run=False)
    assert isinstance(passed, bool)
    assert isinstance(failures, list)
