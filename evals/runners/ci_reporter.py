"""Continuous Integration (CI) reporter.

Formats evaluation results as a Markdown table that gets posted as a comment
on a GitHub Pull Request (PR) by the CI workflow (.github/workflows/eval.yml).

How it fits in the pipeline:
  1. Developer opens a Pull Request (PR) to merge a branch into main.
  2. GitHub Actions (the Continuous Integration system) detects the PR and
     runs the eval workflow automatically.
  3. The eval workflow calls evaluate_response() on every eval case,
     then passes the aggregated scores to format_markdown_report().
  4. The resulting Markdown table is posted as a comment on the PR so
     reviewers can see quality scores before approving the merge.
  5. check_thresholds() decides whether the CI check passes or fails.
     A failing CI check blocks the merge until scores recover.
"""


# Minimum acceptable score per metric.
# Each entry: (metric_key_in_summary, minimum_score, evaluation_tier)
#
# evaluation_tier:
#   "fast" — checked on every CI run (no Large Language Model calls, free)
#   "full" — only checked when the --llm-judge flag is passed to pytest
#             (requires ANTHROPIC_API_KEY, costs tokens, takes longer)
THRESHOLDS = [
    ("avg_tool_selection",   0.70, "fast"),   # Did agent call the right tools?
    ("avg_tool_parameters",  0.75, "fast"),   # Did agent pass the right args?
    ("avg_routing_accuracy", 0.90, "fast"),   # Did root agent pick the right sub-agent?
    ("avg_trajectory",       0.70, "fast"),   # Did agent call tools in the right order?
    ("avg_safety",           0.95, "fast"),   # Near-zero tolerance: no banned content or PII
    ("avg_correctness",      0.60, "fast"),   # Did numeric facts match ground truth?
    ("avg_faithfulness",     0.75, "full"),   # Are all claims grounded in tool outputs?
    ("avg_relevance",        0.70, "full"),   # Did the response answer the actual question?
]


def format_markdown_report(summary: dict, baseline: dict | None = None) -> str:
    """Format aggregated evaluation scores as a Markdown table for the Pull Request comment.

    Args:
        summary: Output of aggregate_results() — scores grouped by agent category.
        baseline: Optional previous run's scores to show improvement/regression diff.

    Returns:
        A Markdown string ready to be posted as a GitHub Pull Request comment.
    """
    lines = [
        "## Agent Evaluation Report",
        "",
        "### Tier 1 — Deterministic (always runs, no Large Language Model cost)",
        "",
        "| Category | Cases | Overall | Tool Selection | Tool Parameters | Routing Accuracy | Trajectory | Traj Coverage | Traj Order | Safety | Correctness |",
        "|----------|-------|---------|----------------|-----------------|------------------|------------|---------------|------------|--------|-------------|",
    ]

    # Sort categories alphabetically; skip the special "_overall" summary key
    categories = sorted(k for k in summary if not k.startswith("_"))

    for category in categories:
        scores = summary[category]
        regression_diff = ""
        if baseline and category in baseline:
            delta = scores["avg_overall"] - baseline[category].get("avg_overall", 0)
            regression_diff = f" ({'+' if delta >= 0 else ''}{delta:.3f})"

        lines.append(
            f"| {category} | {scores['count']} | "
            f"{_cell(scores['avg_overall'])}{regression_diff} | "
            f"{_cell(scores.get('avg_tool_selection', 0))} | "
            f"{_cell(scores.get('avg_tool_parameters', 0))} | "
            f"{_cell(scores.get('avg_routing_accuracy', 0))} | "
            f"{_cell(scores.get('avg_trajectory', 0))} | "
            f"{_subcell(scores.get('avg_trajectory_coverage'))} | "
            f"{_subcell(scores.get('avg_trajectory_order'))} | "
            f"{_cell(scores.get('avg_safety', 0))} | "
            f"{_cell(scores.get('avg_correctness', 0))} |"
        )

    # Append the cross-category overall row
    if "_overall" in summary:
        overall = summary["_overall"]
        lines.append(
            f"| **OVERALL** | {overall['count']} | **{overall['avg_overall']:.3f}** | "
            f"{_cell(overall.get('avg_tool_selection', 0))} | - | "
            f"{_cell(overall.get('avg_routing_accuracy', 0))} | "
            f"{_cell(overall.get('avg_trajectory', 0))} | "
            f"{_subcell(overall.get('avg_trajectory_coverage'))} | "
            f"{_subcell(overall.get('avg_trajectory_order'))} | "
            f"{_cell(overall.get('avg_safety', 0))} | - |"
        )

    # Tier 2 table — only shown when the Large Language Model judge was run
    # (detected by checking if any faithfulness score was recorded)
    llm_judge_was_run = any(
        summary.get(c, {}).get("avg_faithfulness", 0) > 0
        for c in categories
    )
    if llm_judge_was_run:
        lines.extend([
            "",
            "### Tier 2 — Large Language Model Judge (run with --llm-judge flag)",
            "",
            "| Category | Faithfulness | Relevance |",
            "|----------|-------------|-----------|",
        ])
        for category in categories:
            scores = summary[category]
            lines.append(
                f"| {category} | "
                f"{_cell(scores.get('avg_faithfulness', 0))} | "
                f"{_cell(scores.get('avg_relevance', 0))} |"
            )

    # Threshold reference table — tells reviewers what each score must reach
    lines.extend([
        "",
        "### Pass/Fail Thresholds",
        "| Metric | Minimum Score | Evaluation Tier |",
        "|--------|---------------|-----------------|",
    ])
    for metric_key, minimum, tier in THRESHOLDS:
        # Convert "avg_tool_selection" -> "Tool Selection"
        human_label = metric_key.replace("avg_", "").replace("_", " ").title()
        tier_label = "Fast (always)" if tier == "fast" else "Full (--llm-judge)"
        lines.append(f"| {human_label} | >= {minimum:.2f} | {tier_label} |")

    lines.append("\n_Generated by PrimeEV Factory Floor Agent evaluation system_")
    return "\n".join(lines)


def check_thresholds(summary: dict, llm_judge_run: bool = False) -> tuple[bool, list[str]]:
    """Check whether all evaluation scores meet their minimum thresholds.

    Called by the Continuous Integration workflow to decide whether to pass
    or fail the Pull Request check. A failure blocks the merge.

    Args:
        summary: Aggregated scores from aggregate_results().
        llm_judge_run: Whether the Large Language Model judge metrics
                       (faithfulness, relevance) were included in this run.
                       If False, "full" tier thresholds are skipped.

    Returns:
        Tuple of (all_thresholds_passed: bool, failure_messages: list[str]).
        failure_messages is empty when all_thresholds_passed is True.
    """
    failures = []

    for category, scores in summary.items():
        if category.startswith("_"):  # skip the "_overall" aggregate row
            continue
        for metric_key, minimum, tier in THRESHOLDS:
            if tier == "full" and not llm_judge_run:
                continue  # skip Large Language Model metrics when not run
            actual = scores.get(metric_key)
            if actual is not None and actual < minimum:
                human_label = metric_key.replace("avg_", "").replace("_", " ")
                failures.append(
                    f"{category}/{human_label}: {actual:.3f} < {minimum:.3f} (threshold)"
                )

    return len(failures) == 0, failures


def _cell(score: float) -> str:
    """Format a score for a Markdown table cell with visual severity encoding.

    >= 0.80  -> plain text  (passing, no emphasis needed)
    >= 0.65  -> bold        (marginal, draws reviewer attention)
    <  0.65  -> strikethrough (failing threshold, clearly flagged)
    """
    if score >= 0.80:
        return f"{score:.3f}"
    elif score >= 0.65:
        return f"**{score:.3f}**"
    else:
        return f"~~{score:.3f}~~"


def _subcell(score: float | None) -> str:
    """Format a trajectory sub-score cell (informational only, no threshold)."""
    if score is None:
        return "-"
    return f"{score:.3f}"
