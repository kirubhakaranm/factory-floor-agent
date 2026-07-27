"""Clarification grader — checks if the agent asked for missing required info.

Used for CL-* eval cases where the query is intentionally underspecified.
The agent should ask clarifying questions rather than proceeding with assumed values.
"""

import re


def grade_clarification(
    response: str,
    required_clarifications: list[str],
) -> dict:
    """Score whether the agent asked for all required missing information.

    Args:
        response: Agent's response text.
        required_clarifications: List of things the agent must ask about
            (from eval case "required_clarifications" field).

    Returns:
        Dict with score, asked_count, total, missed_clarifications.
    """
    if not required_clarifications:
        return {"score": 1.0, "note": "no required_clarifications defined"}

    # Agent must ask questions — check for question marks
    has_questions = "?" in response
    if not has_questions:
        return {
            "score": 0.0,
            "asked_count": 0,
            "total": len(required_clarifications),
            "missed_clarifications": required_clarifications,
            "note": "response contains no questions",
        }

    response_lower = response.lower()
    asked, missed = [], []

    for clarification in required_clarifications:
        if _clarification_covered(clarification, response_lower):
            asked.append(clarification)
        else:
            missed.append(clarification)

    score = len(asked) / len(required_clarifications)

    return {
        "score": round(score, 3),
        "asked_count": len(asked),
        "total": len(required_clarifications),
        "missed_clarifications": missed,
        "has_questions": has_questions,
    }


def _clarification_covered(clarification: str, response_lower: str) -> bool:
    """Check if a clarification topic is covered in the response."""
    # Extract key topic words from clarification string (skip short/common words)
    stopwords = {"which", "what", "when", "where", "who", "how", "the", "a", "an",
                 "for", "to", "of", "in", "is", "are", "do", "you", "want", "need"}
    words = [
        w.strip("?.,:")
        for w in clarification.lower().split()
        if len(w) > 3 and w.lower() not in stopwords
    ]

    if not words:
        return False

    # Check how many key words appear in response
    hits = sum(1 for w in words if w in response_lower)
    return hits / len(words) >= 0.4
