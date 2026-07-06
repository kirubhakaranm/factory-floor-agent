"""Hallucination grader — detects claims not supported by tool call outputs."""

import re


def grade_hallucination(
    response: str,
    tool_outputs: list[str],
) -> dict:
    """Score hallucination risk — are factual claims backed by tool data?

    Identifies numeric claims and specific factual assertions in the response,
    then checks if supporting evidence exists in tool outputs.

    Score: 1.0 = no hallucinations, 0.0 = all claims hallucinated.

    Args:
        response: Agent's response text
        tool_outputs: List of tool output strings

    Returns:
        Dict with score, total_claims, supported, unsupported, examples
    """
    if not tool_outputs:
        # No tool outputs means we can't verify — conservative score
        return {
            "score": 0.5,
            "reason": "No tool outputs to verify against",
            "total_claims": 0,
        }

    combined_output = " ".join(str(o) for o in tool_outputs).lower()

    # Extract factual claims from response
    claims = _extract_claims(response)

    if not claims:
        return {"score": 1.0, "total_claims": 0, "supported": 0, "unsupported": 0}

    supported = []
    unsupported = []

    for claim in claims:
        if _is_supported(claim, combined_output):
            supported.append(claim)
        else:
            unsupported.append(claim)

    total = len(claims)
    score = len(supported) / total if total > 0 else 1.0

    return {
        "score": round(score, 3),
        "total_claims": total,
        "supported": len(supported),
        "unsupported": len(unsupported),
        "unsupported_examples": unsupported[:5],
        "hallucination_rate": round(1.0 - score, 3),
    }


def _extract_claims(text: str) -> list[str]:
    """Extract factual claims — sentences with numbers, specific IDs, or definitive statements."""
    sentences = re.split(r"[.!?]\s+", text)
    claims = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 15:
            continue

        has_number = bool(re.search(r"\b\d+\.?\d*\b", sentence))
        has_id = bool(re.search(r"[A-Z]{3}-\d{2}", sentence))
        has_definitive = any(word in sentence.lower() for word in [
            "is ", "was ", "are ", "were ", "shows ", "indicates ",
            "caused by", "resulted in", "equals", "measured at",
        ])

        if has_number or has_id or has_definitive:
            claims.append(sentence)

    return claims


def _is_supported(claim: str, tool_output: str) -> bool:
    """Check if a claim has supporting evidence in tool outputs."""
    claim_lower = claim.lower()

    # Extract key terms from claim
    numbers = re.findall(r"\b\d+\.?\d*\b", claim)
    ids = re.findall(r"[A-Z]{3}-\d{2}-?[A-Z]*-?[A-Z]*\d*", claim)

    # Check if numbers from claim appear in tool output
    number_hits = sum(1 for n in numbers if n in tool_output)

    # Check if IDs from claim appear in tool output
    id_hits = sum(1 for i in ids if i.lower() in tool_output)

    # Check key term overlap
    words = [w for w in claim_lower.split() if len(w) > 4]
    word_hits = sum(1 for w in words if w in tool_output) if words else 0
    word_coverage = word_hits / max(len(words), 1)

    # Claim is supported if numbers/IDs match OR sufficient keyword overlap
    if numbers and number_hits > 0:
        return True
    if ids and id_hits > 0:
        return True
    if word_coverage >= 0.3:
        return True

    return False
