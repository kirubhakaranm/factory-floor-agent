"""Response validation — hallucination checks, citation verification."""


def check_claims_supported(response_text: str, tool_outputs: list[str]) -> dict:
    """Check if claims in the response are supported by tool call outputs.

    Args:
        response_text: The agent's response text
        tool_outputs: List of tool output strings from the conversation

    Returns:
        Dict with supported_claims, unsupported_claims, and hallucination_risk
    """
    tool_text = " ".join(tool_outputs).lower()
    sentences = [s.strip() for s in response_text.split(".") if len(s.strip()) > 20]

    supported = []
    unsupported = []

    for sentence in sentences:
        words = sentence.lower().split()
        # Check if key words from the claim appear in tool outputs
        numeric_words = [w for w in words if any(c.isdigit() for c in w)]
        if numeric_words:
            matches = sum(1 for w in numeric_words if w in tool_text)
            if matches > 0:
                supported.append(sentence)
            else:
                unsupported.append(sentence)

    total = len(supported) + len(unsupported)
    hallucination_risk = len(unsupported) / max(total, 1)

    return {
        "supported_claims": len(supported),
        "unsupported_claims": len(unsupported),
        "hallucination_risk": round(hallucination_risk, 2),
        "unsupported_details": unsupported[:5],
    }


def validate_confidence_score(stated_confidence: float, evidence_count: int) -> dict:
    """Validate that a stated confidence score is reasonable given the evidence.

    Args:
        stated_confidence: The confidence score the agent stated (0.0-1.0)
        evidence_count: Number of evidence items cited

    Returns:
        Assessment of whether confidence is calibrated
    """
    if evidence_count == 0 and stated_confidence > 0.3:
        return {
            "calibrated": False,
            "issue": "High confidence with no evidence cited",
            "suggestion": "Reduce confidence or gather more evidence",
        }
    if evidence_count >= 3 and stated_confidence < 0.3:
        return {
            "calibrated": False,
            "issue": "Low confidence despite multiple evidence items",
            "suggestion": "Review if evidence supports a higher confidence",
        }
    return {"calibrated": True, "issue": None}
