"""Metric 4: Correctness — two tiers.

data facts    →  strict ±2% numeric match (always, free)
              These come from the GT generator querying the live DB — exact numbers
              the agent must reproduce by actually calling the right tools.

domain facts  →  LLM judge (or keyword fallback when use_llm=False)
              Behavioral rubric criteria written by hand — things like "should compare
              to 75% target". Require semantic understanding, not exact matching.
"""

import re

from evals.graders.llm_judge import judge_correctness as _llm_judge


# ── Schema normalisation ────────────────────────────────────────────────────

def _split_key_facts(ground_truth: dict) -> tuple[list[str], list[str]]:
    """Return (domain_facts, data_facts) from ground_truth.key_facts."""
    key_facts = ground_truth.get("key_facts", [])

    if isinstance(key_facts, list):
        return key_facts, []

    if isinstance(key_facts, dict):
        return (
            key_facts.get("domain", []),
            key_facts.get("data", []),
        )

    return [], []


# ── Tier 1: strict numeric match for DB-sourced data facts ─────────────────

def _extract_numbers(text: str) -> list[float]:
    """Extract all numeric values from a string as floats."""
    return [float(n) for n in re.findall(r"\b\d+\.?\d*\b", text)]


def _grade_data_facts(response: str, data_facts: list[str]) -> dict:
    """Every number in each expected fact must appear in the response within ±2%."""
    if not data_facts:
        return {"score": 1.0, "matched": 0, "total": 0, "missed_facts": []}

    matched, missed = [], []
    response_numbers = _extract_numbers(response)

    for fact in data_facts:
        expected_nums = _extract_numbers(fact)
        if not expected_nums:
            matched.append(fact)
            continue

        all_found = True
        for expected in expected_nums:
            tolerance = max(abs(expected) * 0.02, 0.5)
            found = any(abs(actual - expected) <= tolerance for actual in response_numbers)
            if not found:
                all_found = False
                break

        (matched if all_found else missed).append(fact)

    return {
        "score": round(len(matched) / len(data_facts), 3),
        "matched": len(matched),
        "total": len(data_facts),
        "missed_facts": missed,
    }


# ── Tier 2 fallback: keyword match for domain facts (no LLM) ───────────────

def _grade_domain_facts_keyword(response: str, domain_facts: list[str]) -> dict:
    """Check if ≥40% of meaningful words from each domain fact appear in the response."""
    if not domain_facts:
        return {"score": 1.0, "matched": 0, "total": 0, "missed_facts": []}

    response_lower = response.lower()
    matched, missed = [], []

    for fact in domain_facts:
        words = [w for w in fact.lower().split() if len(w) > 4]
        if not words:
            matched.append(fact)
            continue
        hits = sum(1 for w in words if w in response_lower)
        (matched if hits / len(words) >= 0.4 else missed).append(fact)

    return {
        "score": round(len(matched) / len(domain_facts), 3),
        "matched": len(matched),
        "total": len(domain_facts),
        "missed_facts": missed,
        "llm_judge": False,
    }


# ── Public grader ───────────────────────────────────────────────────────────

def grade_correctness(
    response: str,
    ground_truth: dict,
    tool_outputs: list[str] | None = None,
    use_llm: bool = True,
) -> dict:
    """Score correctness across two tiers.

    data facts    → strict ±2% numeric match (always, free)
    domain facts  → LLM judge when use_llm=True, keyword fallback otherwise
    """
    domain_facts, data_facts = _split_key_facts(ground_truth)

    # Tier 1: data facts
    data_result = _grade_data_facts(response, data_facts)

    # Tier 2: domain facts
    if domain_facts:
        if use_llm:
            domain_result = _llm_judge(response, domain_facts, tool_outputs or [])
        else:
            domain_result = _grade_domain_facts_keyword(response, domain_facts)
        domain_score = domain_result.get("score", 1.0)
    else:
        domain_result = {"score": 1.0, "note": "no domain facts defined"}
        domain_score = 1.0

    # Combine — data facts weighted 1.5× (exact GT is harder to satisfy)
    n_data = len(data_facts)
    n_domain = len(domain_facts)

    if n_data == 0 and n_domain == 0:
        combined = 1.0
    elif n_data == 0:
        combined = domain_score
    elif n_domain == 0:
        combined = data_result["score"]
    else:
        combined = (
            data_result["score"] * n_data * 1.5 + domain_score * n_domain
        ) / (n_data * 1.5 + n_domain)

    return {
        "score": round(combined, 3),
        "data_score": data_result["score"],
        "data_facts_checked": n_data,
        "data_details": data_result,
        "domain_score": domain_score,
        "domain_facts_checked": n_domain,
        "domain_details": domain_result,
    }
