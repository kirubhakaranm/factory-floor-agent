"""Correctness grader — checks if key facts from ground truth appear in agent response."""


def grade_correctness(
    response: str,
    ground_truth: dict,
    tool_outputs: list[str] | None = None,
) -> dict:
    """Score response correctness based on key facts.

    Checks if each expected key fact is present in the response using
    keyword matching. Returns a score 0.0-1.0.

    Args:
        response: Agent's response text
        ground_truth: Dict with 'key_facts' list of expected facts
        tool_outputs: Optional list of tool output strings

    Returns:
        Dict with score, matched_facts, missed_facts
    """
    key_facts = ground_truth.get("key_facts", [])
    if not key_facts:
        return {"score": 1.0, "matched": [], "missed": [], "total": 0}

    response_lower = response.lower()
    matched = []
    missed = []

    for fact in key_facts:
        # Extract key terms from the fact (words > 4 chars, not common words)
        stop_words = {"should", "about", "their", "which", "would", "could", "these", "there",
                      "where", "being", "might", "after", "before", "using", "based"}
        keywords = [
            w.strip(".,;:()\"'")
            for w in fact.lower().split()
            if len(w) > 4 and w not in stop_words
        ]

        # Check if enough keywords appear in response
        if not keywords:
            matched.append(fact)
            continue

        hits = sum(1 for kw in keywords if kw in response_lower)
        coverage = hits / len(keywords)

        if coverage >= 0.4:  # At least 40% of keywords present
            matched.append(fact)
        else:
            missed.append(fact)

    score = len(matched) / len(key_facts) if key_facts else 1.0

    return {
        "score": round(score, 3),
        "matched_facts": len(matched),
        "missed_facts": len(missed),
        "total_facts": len(key_facts),
        "matched": matched,
        "missed": missed,
    }
