"""Confidence calibration grader — checks if stated confidence matches evidence quality."""

import re


def grade_confidence_calibration(
    response: str,
    correctness_score: float,
    tool_call_count: int,
) -> dict:
    """Score confidence calibration — is the agent's stated confidence reasonable?

    Penalizes overconfidence more than underconfidence (overconfident agents
    are more dangerous in manufacturing).

    Args:
        response: Agent's response text
        correctness_score: Score from correctness grader (0.0-1.0)
        tool_call_count: Number of tool calls made

    Returns:
        Dict with score, stated_confidence, calibration_error
    """
    # Extract stated confidence from response
    confidence_patterns = [
        r"confidence[:\s]+(\d+\.?\d*)%",
        r"confidence[:\s]+(\d+\.?\d*)\s*/\s*1",
        r"(\d+\.?\d*)%?\s*confiden",
        r"confidence.*?(\d+\.?\d*)",
    ]

    stated = None
    for pattern in confidence_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            stated = val / 100 if val > 1 else val
            break

    if stated is None:
        # No confidence stated — mild penalty
        return {
            "score": 0.6,
            "stated_confidence": None,
            "reason": "No confidence score stated in response",
        }

    stated = max(0.0, min(1.0, stated))

    # Expected confidence based on evidence
    if tool_call_count >= 4 and correctness_score >= 0.8:
        expected_range = (0.7, 1.0)
    elif tool_call_count >= 2 and correctness_score >= 0.5:
        expected_range = (0.4, 0.8)
    else:
        expected_range = (0.1, 0.5)

    # Calibration error
    if stated < expected_range[0]:
        error = expected_range[0] - stated  # underconfident
        penalty = error * 0.5  # mild penalty
    elif stated > expected_range[1]:
        error = stated - expected_range[1]  # overconfident
        penalty = error * 1.5  # harsh penalty for overconfidence
    else:
        error = 0.0
        penalty = 0.0

    score = max(0.0, 1.0 - penalty)

    return {
        "score": round(score, 3),
        "stated_confidence": round(stated, 2),
        "expected_range": [round(expected_range[0], 2), round(expected_range[1], 2)],
        "calibration_error": round(error, 3),
        "calibrated": error < 0.15,
    }
