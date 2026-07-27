"""Shared LLM judge infrastructure — used only when exact match / rules can't work.

Uses claude-haiku-4-5 (cheapest) with structured JSON output.
Falls back to a heuristic score if ANTHROPIC_API_KEY is not set or the call fails.
"""

import json
import os
import re

# Maximum characters embedded into any judge prompt — prevents the LLM from
# generating malformed JSON due to unescaped quotes/newlines in long inputs.
_MAX_RESPONSE_CHARS = 2000
_MAX_TOOL_OUTPUT_CHARS = 4000


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending a character-count suffix when cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"… [truncated {len(text) - max_chars} chars]"


def _client() -> "anthropic.Anthropic":
    """Return an authenticated Anthropic client using ANTHROPIC_API_KEY."""
    import anthropic

    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json(raw: str) -> dict:
    """Extract JSON from LLM output with three fallback strategies."""
    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown fences, try each fenced block
    if "```" in raw:
        for block in raw.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith("{"):
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    pass

    # Strategy 3: extract outermost {...} with regex (handles preamble/postamble)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM response: {raw[:300]}")


def _call(prompt: str, fallback: dict) -> dict:
    """Call LLM judge. Returns structured dict or fallback on any error."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {**fallback, "llm_judge": False, "reason": "no ANTHROPIC_API_KEY"}
    try:
        client = _client()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        return {**_extract_json(raw), "llm_judge": True}
    except Exception as e:
        return {**fallback, "llm_judge": False, "reason": str(e)}


# ── Public judge functions ──────────────────────────────────────────────────


def judge_faithfulness(response: str, tool_outputs: list[str], query: str = "") -> dict:
    """Are all factual claims in the response grounded in tool output or the user's query?"""
    truncated_outputs = [_truncate(o, _MAX_TOOL_OUTPUT_CHARS) for o in tool_outputs[:5]]
    context = "\n---\n".join(truncated_outputs)
    response = _truncate(response, _MAX_RESPONSE_CHARS)
    query_section = (
        f"\nUSER QUERY (also a valid source — facts stated by the user may be used as-is):\n{query}\n"
        if query
        else ""
    )
    prompt = f"""You are evaluating an AI agent's response for faithfulness to its sources.

TOOL OUTPUTS (primary source of truth):
{context}
{query_section}
AGENT RESPONSE:
{response}

Task: Identify every factual claim in the response (numeric values, status assertions, causal statements, entity properties). For each claim determine if it is directly supported by EITHER the tool outputs OR the user's query above. Facts the user explicitly stated in their query are considered grounded — the agent is not hallucinating when it uses them.

IMPORTANT GROUNDING RULES:
- Tool outputs above may be truncated. If a claim is consistent with data visible in the truncated output AND plausibly continues the same pattern (e.g., another row from the same table), treat it as SUPPORTED — do not penalize for truncation.
- Agent system-knowledge claims (factory topology, machine IDs, tool names, internal architecture details) do NOT count as factual claims — ignore them for faithfulness scoring.
- Only flag a claim as UNSUPPORTED if it contradicts the tool outputs or invents specific values (dates, numbers, status) with no basis in the visible data.

Return ONLY valid JSON (no markdown). List at most 5 unsupported claims (omit the rest):
{{"score": <float 0.0-1.0>, "total_claims": <int>, "supported": <int>, "unsupported_claims": [<str up to 5>], "reasoning": <str>}}

Score = supported / total_claims. If no factual claims exist return score 1.0."""

    return _call(
        prompt,
        {
            "score": 0.5,
            "total_claims": 0,
            "supported": 0,
            "unsupported_claims": [],
            "reasoning": "fallback",
        },
    )


def judge_relevance(query: str, response: str) -> dict:
    """Does the response actually answer the question asked?"""
    response = _truncate(response, _MAX_RESPONSE_CHARS)
    prompt = f"""You are evaluating if an AI agent's response answers the user's question.

USER QUESTION:
{query}

AGENT RESPONSE:
{response}

Task: Score how directly and completely the response addresses what was asked.
- 1.0 = fully answers the question with appropriate detail
- 0.7 = answers but misses minor aspects
- 0.4 = partially answers, drifts to a related topic
- 0.0 = completely off-topic or refuses without reason

IMPORTANT — PrimeEV Motors domain context (apply these rules before evaluating):
- Vehicle VIN format: PEF-{{MODEL}}-{{YY}}-{{SEQ}} (e.g. PEF-SD100-26-002000). This is a valid internal VIN format.
- Equipment/machine IDs follow a different format: {{STAGE}}-{{NN}}-{{TYPE}}-{{MACHINE}} (e.g. STP-01-PRS-HYP01, WLD-01-UBD-RBT02). These are NOT VINs — they are machine identifiers. Do NOT apply VIN format validation to machine IDs.
- When the agent presents specific operational data (batch IDs, timestamps, inspection records, sensor values, production history), ASSUME this data was retrieved from a real system tool call — do NOT flag it as "fabricated" unless the values are clearly impossible (e.g. future dates on completed records, contradictory states).
- The following are VALID, high-relevance responses (score >= 0.8) even if they don't provide the data requested:
  - Agent states the requested data does not exist in the system (e.g. lot not found, VIN not found) — this IS answering the question.
  - Agent refuses to fabricate or guess data it doesn't have — this is correct manufacturing AI behavior, not evasion.
  - Agent explains WHY data is unavailable and what the user can do instead.
Only score low if the agent is off-topic, ignores the question entirely, or refuses without any explanation.

Return ONLY valid JSON:
{{"score": <float 0.0-1.0>, "answered_question": <bool>, "issues": [<str>], "reasoning": <str>}}"""

    return _call(
        prompt,
        {
            "score": 0.5,
            "answered_question": None,
            "issues": [],
            "reasoning": "fallback",
        },
    )


def judge_correctness(
    response: str, key_facts: list[str], tool_outputs: list[str]
) -> dict:
    """Are the agent's explanations and conclusions correct given ground truth?"""
    facts_text = "\n".join(f"- {f}" for f in key_facts)
    truncated_outputs = [_truncate(o, _MAX_TOOL_OUTPUT_CHARS) for o in tool_outputs[:5]]
    context = "\n---\n".join(truncated_outputs)
    response = _truncate(response, _MAX_RESPONSE_CHARS)
    prompt = f"""You are evaluating the factual correctness of an AI agent's response.

GROUND TRUTH FACTS:
{facts_text}

TOOL OUTPUTS (supporting data):
{context}

AGENT RESPONSE:
{response}

Task: Check if the agent's conclusions and explanations are consistent with the ground truth facts. Focus on directional correctness (e.g. "increasing" vs "decreasing"), threshold assessments (e.g. "above spec" vs "within spec"), and causal attribution.

Return ONLY valid JSON. List at most 5 items in each claims array:
{{"score": <float 0.0-1.0>, "incorrect_claims": [<str up to 5>], "correct_claims": [<str up to 5>], "reasoning": <str>}}"""

    return _call(
        prompt,
        {
            "score": 0.5,
            "incorrect_claims": [],
            "correct_claims": [],
            "reasoning": "fallback",
        },
    )


def judge_multi_turn_coherence(history: list[dict], response: str) -> dict:
    """Does the response maintain coherence with prior conversation turns?"""
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
    )
    prompt = f"""You are evaluating conversational coherence for an AI agent.

CONVERSATION HISTORY:
{history_text}

CURRENT RESPONSE:
{response}

Task: Check if the response:
1. Correctly references context established in prior turns (entities, metrics, decisions)
2. Does not contradict prior statements without explanation
3. Maintains consistent terminology for the same entities
4. Answers follow-up questions in context (not treating them as standalone queries)

Return ONLY valid JSON:
{{"score": <float 0.0-1.0>, "issues": [<str>], "context_used": <bool>, "reasoning": <str>}}"""

    return _call(
        prompt,
        {"score": 0.5, "issues": [], "context_used": None, "reasoning": "fallback"},
    )
