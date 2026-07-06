"""Action validity grader — checks if recommended actions are valid per SOPs and specs."""

import re


def grade_action_validity(
    response: str,
    ground_truth: dict,
    tool_calls: list[dict],
) -> dict:
    """Score whether recommended actions are valid and complete.

    Checks:
    1. Actions are specific (not generic/vague)
    2. Actions reference correct entities (machine IDs, part numbers)
    3. Required action tool was called if creating documents
    4. Safety-critical items are flagged

    Args:
        response: Agent's response text
        ground_truth: Expected ground truth with key_facts
        tool_calls: List of tool calls made

    Returns:
        Dict with score, specificity, completeness, safety_flagged
    """
    score_components = []

    # 1. Specificity — does response include specific actionable items?
    action_keywords = [
        "replace", "inspect", "adjust", "calibrate", "schedule", "increase",
        "decrease", "reduce", "clean", "flush", "check", "verify", "repair",
        "install", "remove", "update", "train", "monitor",
    ]
    action_count = sum(
        1 for kw in action_keywords
        if re.search(rf"\b{kw}\b", response, re.IGNORECASE)
    )
    specificity = min(1.0, action_count / 3)
    score_components.append(specificity)

    # 2. Entity references — are actions tied to specific machines/parts?
    entity_patterns = [
        r"[A-Z]{3}-\d{2}-[A-Z]{3}",  # station IDs
        r"[A-Z]{3}-\d{2}-[A-Z]{3}-[A-Z]{3}\d{2}",  # machine IDs
        r"SP-[A-Z]{3}-\d{3}",  # spare part numbers
        r"SUP-[A-Z]{3}\d{2}",  # supplier IDs
    ]
    entity_refs = sum(len(re.findall(p, response)) for p in entity_patterns)
    entity_score = min(1.0, entity_refs / 2)
    score_components.append(entity_score)

    # 3. Tool call completeness — for action-type queries, was the action tool called?
    expected_recommendation = ground_truth.get("expected_recommendation", "")
    action_tools_called = [
        tc for tc in tool_calls
        if tc.get("tool", "").startswith("create_") or tc.get("tool") == "schedule_maintenance"
    ]

    if expected_recommendation:
        # Check if recommendation keywords appear in response
        rec_words = [w for w in expected_recommendation.lower().split() if len(w) > 4]
        rec_hits = sum(1 for w in rec_words if w in response.lower())
        rec_coverage = rec_hits / max(len(rec_words), 1)
        score_components.append(rec_coverage)

    # 4. Prioritization — does response have structured recommendations?
    has_priority = bool(re.search(
        r"(immediate|short.?term|long.?term|first|then|priority|step\s*\d|1\.|2\.|3\.)",
        response, re.IGNORECASE
    ))
    score_components.append(1.0 if has_priority else 0.3)

    # 5. Safety flagging
    safety_keywords = ["safety", "critical", "hazard", "urgent", "immediately", "stop production"]
    safety_flagged = any(kw in response.lower() for kw in safety_keywords)

    overall = sum(score_components) / len(score_components) if score_components else 0.5

    return {
        "score": round(overall, 3),
        "specificity": round(specificity, 3),
        "entity_references": entity_refs,
        "action_tools_called": len(action_tools_called),
        "has_prioritization": has_priority,
        "safety_flagged": safety_flagged,
    }
