"""Shared output formatting — evidence chains, citations, confidence display."""


def format_evidence_chain(evidence: list[dict]) -> str:
    """Format a list of evidence items into a readable chain.

    Each evidence item: {"source": str, "finding": str, "strength": "strong"|"moderate"|"weak"}
    """
    if not evidence:
        return "No evidence collected."

    lines = ["**Evidence Chain:**"]
    for e in evidence:
        strength_icon = {
            "strong": "[STRONG]",
            "moderate": "[MODERATE]",
            "weak": "[WEAK]",
        }.get(e.get("strength", ""), "[?]")
        lines.append(f"  {strength_icon} {e['finding']} (Source: {e['source']})")

    return "\n".join(lines)


def format_confidence(score: float, reasoning: str = "") -> str:
    """Format a confidence score with visual indicator."""
    if score >= 0.8:
        level = "HIGH"
    elif score >= 0.5:
        level = "MODERATE"
    else:
        level = "LOW"

    result = f"**Confidence: {score:.0%} ({level})**"
    if reasoning:
        result += f"\n  Basis: {reasoning}"
    return result


def format_citation(source_type: str, source_id: str, detail: str) -> str:
    """Format a data citation for agent responses."""
    return f"[Source: {source_type}, {source_id}, {detail}]"


def format_recommendation(
    immediate: str | None = None,
    short_term: str | None = None,
    long_term: str | None = None,
) -> str:
    """Format a prioritized recommendation."""
    lines = ["**Recommendations:**"]
    if immediate:
        lines.append(f"  1. **IMMEDIATE**: {immediate}")
    if short_term:
        lines.append(f"  2. **Short-term**: {short_term}")
    if long_term:
        lines.append(f"  3. **Long-term**: {long_term}")
    return "\n".join(lines)
