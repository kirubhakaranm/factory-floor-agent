"""Pytest configuration for the eval suite.

pytest_addoption must live in conftest.py so options are registered before
any test module is collected.

Parallel-safe result collection:
  Each live eval test writes its result to a per-case JSON file under
  .eval_runs/<run_name>/<case_id>.json. Set EVAL_RUN_NAME env var to name
  the run (e.g. "haiku-round1", "sonnet-round1"). Defaults to "latest".
  Results are never wiped between named runs — only "latest" is cleared.
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from evals.runners.eval_runner import aggregate_results
from evals.runners.ci_reporter import check_thresholds, format_markdown_report

_RUNS_DIR = Path(__file__).parent / ".eval_runs"

# Resolve the results directory for this run.
# EVAL_RUN_NAME="haiku-round1"  → .eval_runs/haiku-round1/
# EVAL_RUN_NAME unset            → .eval_runs/latest/  (cleared each run)
_RUN_NAME = os.environ.get("EVAL_RUN_NAME", "latest")
RESULTS_DIR = _RUNS_DIR / _RUN_NAME


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register --live and --llm-judge CLI flags for the eval suite."""
    parser.addoption(
        "--live", action="store_true", default=False,
        help="Run all 100 eval cases against the live agent (requires ANTHROPIC_API_KEY)",
    )
    parser.addoption(
        "--llm-judge", action="store_true", default=False,
        help="Enable LLM judge metrics: faithfulness, relevance, multi-turn coherence",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Prepare the results directory for this run."""
    if not hasattr(config, "workerinput"):
        # Only clear "latest" — named runs are kept forever for comparison.
        if _RUN_NAME == "latest" and RESULTS_DIR.exists():
            shutil.rmtree(RESULTS_DIR)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def write_result(result: dict) -> None:
    """Write one eval result to its own JSON file (called from each worker)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{result['case_id']}.json"
    path.write_text(json.dumps(result, indent=2))


_REPORT_PATH = Path(__file__).parent.parent / "eval_report.md"


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """On the controller: read all per-case result files and print + save aggregate report."""
    if hasattr(session.config, "workerinput"):
        return

    result_files = list(RESULTS_DIR.glob("*.json"))
    if not result_files:
        return

    use_llm = session.config.getoption("--llm-judge", default=False)

    results = [json.loads(f.read_text()) for f in sorted(result_files)]
    summary = aggregate_results(results)
    report = format_markdown_report(summary)
    passed, failures = check_thresholds(summary, llm_judge_run=use_llm)

    model = os.environ.get("AGENT_MODEL", "default")
    header = f"Run: {_RUN_NAME} | Model: {model} | Cases: {len(results)}"
    threshold_section = ""
    if failures:
        threshold_section = "\n\n### Failed Thresholds\n" + "\n".join(f"- ❌ {f}" for f in failures)
    else:
        threshold_section = "\n\n### Thresholds\n✅ All thresholds passed."

    full_report = f"{report}{threshold_section}\n\n_{header}_"

    # Save to disk for the GitHub Actions PR comment step
    _REPORT_PATH.write_text(full_report, encoding="utf-8")

    print(f"\n\n{header}")
    print("=" * 72)
    print(report)
    if failures:
        print("\nFAILED THRESHOLDS:")
        for f in failures:
            print(f"  FAIL {f}")
    else:
        print("\nAll thresholds passed.")
    print("=" * 72)
    print(f"Report saved to {_REPORT_PATH}")
