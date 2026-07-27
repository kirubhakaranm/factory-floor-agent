"""Metric 6: Routing Accuracy — exact match.

Binary: did the root agent send the query to the correct sub-agent?
"""


def grade_routing_accuracy(
    expected_agent: str,
    actual_tool_calls: list[dict],
    wrong_agents: list[str] | None = None,
    agents_invoked: set[str] | None = None,
) -> dict:
    """Score routing accuracy.

    Args:
        expected_agent: Agent name the query should be routed to.
        actual_tool_calls: List of {tool, args, agent} dicts from the run.
        wrong_agents: Agent names that must NOT be invoked (from routing.json).
        agents_invoked: Set of agent names that were invoked (from transfer_to_agent
                        extraction in the runner — used as fallback when sub-agent
                        makes no tool calls but does respond with text).

    Returns:
        Dict with score (1.0 or 0.0), correct, actual_agents.
    """
    if not expected_agent:
        return {"score": 1.0, "correct": True, "note": "no expected_agent specified"}

    # "root_agent" in eval cases is an alias for the root agent's actual ADK name.
    # The root agent is always present in agents_invoked as "primeev_factory_agent".
    ROOT_AGENT_NAMES = {"root_agent", "primeev_factory_agent"}
    if expected_agent in ROOT_AGENT_NAMES:
        expected_agent = "primeev_factory_agent"

    # Primary: agents identified from their own tool calls
    actual_agents = {tc.get("agent", "") for tc in actual_tool_calls}
    # Fallback: agents captured via transfer_to_agent extraction or event.author
    if agents_invoked:
        actual_agents |= agents_invoked
    actual_agents.discard("")

    correct = expected_agent in actual_agents

    # Hard fail if a wrong agent was invoked regardless of expected match
    wrong_hit = [a for a in (wrong_agents or []) if a in actual_agents]
    if wrong_hit:
        return {
            "score": 0.0,
            "correct": False,
            "expected_agent": expected_agent,
            "actual_agents": sorted(actual_agents),
            "wrong_agents_invoked": wrong_hit,
            "note": "query was routed to a known-wrong agent",
        }

    return {
        "score": 1.0 if correct else 0.0,
        "correct": correct,
        "expected_agent": expected_agent,
        "actual_agents": sorted(actual_agents),
    }
