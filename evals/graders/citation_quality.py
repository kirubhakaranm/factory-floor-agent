"""Citation quality grader — checks if response cites data sources and tool outputs."""

import re


def grade_citation_quality(
    response: str,
    tool_calls: list[dict],
    tool_outputs: list[str],
) -> dict:
    """Score how well the response cites its data sources.

    Checks for:
    1. References to specific tool calls or data sources
    2. Numeric values that appear in tool outputs
    3. Station/machine IDs referenced from actual data

    Args:
        response: Agent's response text
        tool_calls: List of {tool, args} dicts from the conversation
        tool_outputs: List of tool output strings

    Returns:
        Dict with score, citation_count, data_references
    """
    if not tool_calls:
        return {"score": 0.5, "reason": "No tool calls made — cannot verify citations"}

    score_components = []

    # 1. Does response reference tool names or data sources?
    source_patterns = [
        r"\[source[:\s]",
        r"according to",
        r"data shows",
        r"based on",
        r"sensor data",
        r"from the",
        r"indicates",
        r"records show",
        r"history shows",
    ]
    source_refs = sum(1 for p in source_patterns if re.search(p, response, re.IGNORECASE))
    source_score = min(1.0, source_refs / 3)
    score_components.append(source_score)

    # 2. Does response include specific IDs (machine, station, part numbers)?
    id_patterns = [
        r"STP-\d{2}-[A-Z]{3}",
        r"WLD-\d{2}-[A-Z]{3}",
        r"PNT-\d{2}-[A-Z]{3}",
        r"ASM-\d{2}-[A-Z]{3}",
        r"QAT-\d{2}-[A-Z]{3}",
        r"[A-Z]{3}-\d{2}-[A-Z]{3}-[A-Z]{3}\d{2}",
        r"SUP-[A-Z]{3}\d{2}",
        r"PEF-[A-Z]{2}\d{3}",
    ]
    id_count = sum(len(re.findall(p, response)) for p in id_patterns)
    id_score = min(1.0, id_count / 2)
    score_components.append(id_score)

    # 3. Does response include numeric values?
    numbers = re.findall(r"\b\d+\.?\d*\b", response)
    numeric_score = min(1.0, len(numbers) / 3)
    score_components.append(numeric_score)

    # 4. Tool call coverage — did the response use multiple tools?
    tool_diversity = min(1.0, len(set(tc.get("tool", "") for tc in tool_calls)) / 2)
    score_components.append(tool_diversity)

    overall = sum(score_components) / len(score_components)

    return {
        "score": round(overall, 3),
        "source_references": source_refs,
        "entity_ids_cited": id_count,
        "numeric_values": len(numbers),
        "tools_used": len(tool_calls),
        "unique_tools": len(set(tc.get("tool", "") for tc in tool_calls)),
    }
