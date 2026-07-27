"""Metric 5: Relevance — LLM judge.

Only an LLM can judge "did this response answer the actual question?"
No keyword rule can distinguish "answers the question asked" from "talks about the same topic."
"""

from evals.graders.llm_judge import judge_relevance


def grade_relevance(
    query: str,
    response: str,
    use_llm: bool = True,
) -> dict:
    """Score whether the response directly answers the query.

    Args:
        query: The user's original question.
        response: Agent's response text.
        use_llm: If False, returns 0.5 (use in fast CI tier).

    Returns:
        Dict with score, answered_question, issues, reasoning.
    """
    if not use_llm:
        return {
            "score": 0.5,
            "note": "LLM judge skipped (use_llm=False)",
            "llm_judge": False,
        }

    return judge_relevance(query, response)
