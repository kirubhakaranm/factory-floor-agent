"""Metric 3: Faithfulness — LLM judge.

Every factual claim in the response must be traceable to a tool output.
No regex can do this reliably — needs semantic understanding.
"""

from evals.graders.llm_judge import judge_faithfulness


def grade_faithfulness(
    response: str,
    tool_outputs: list[str],
    use_llm: bool = True,
    query: str = "",
) -> dict:
    """Score faithfulness of response to tool outputs and user query.

    Args:
        response: Agent's response text.
        tool_outputs: Raw tool output strings from the run.
        use_llm: If False, returns a fixed 0.5 (useful for fast CI tier).
        query: Original user query — facts stated here are valid sources too.

    Returns:
        Dict with score, total_claims, supported, unsupported_claims.
    """
    if not tool_outputs:
        return {
            "score": 0.5,
            "total_claims": 0,
            "note": "no tool outputs — cannot verify faithfulness",
            "llm_judge": False,
        }

    if not use_llm:
        return {
            "score": 0.5,
            "note": "LLM judge skipped (use_llm=False)",
            "llm_judge": False,
        }

    return judge_faithfulness(response, tool_outputs, query=query)
