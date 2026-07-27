"""Metric 9: Multi-turn Coherence — LLM judge.

Single-turn evals can skip this (score defaults to 1.0).
Only applies when the eval case has a `conversation_history` field.
"""

from evals.graders.llm_judge import judge_multi_turn_coherence


def grade_multi_turn_coherence(
    response: str,
    conversation_history: list[dict] | None,
    use_llm: bool = True,
) -> dict:
    """Score multi-turn coherence.

    Args:
        response: The agent's current response.
        conversation_history: Prior turns as [{role, content}] dicts.
                              If None or empty, returns 1.0 (not applicable).
        use_llm: If False, returns 0.5.

    Returns:
        Dict with score, issues, context_used, reasoning.
    """
    if not conversation_history:
        return {"score": 1.0, "note": "single-turn — coherence not applicable"}

    if not use_llm:
        return {
            "score": 0.5,
            "note": "LLM judge skipped (use_llm=False)",
            "llm_judge": False,
        }

    return judge_multi_turn_coherence(conversation_history, response)
