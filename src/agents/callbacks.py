"""Agent callbacks — logging, guardrails, and metrics."""

import time
import logging

logger = logging.getLogger("primeev.agents")


class AgentCallbackHandler:
    """Tracks agent execution for logging and monitoring."""

    def __init__(self) -> None:
        self._start_times: dict[str, float] = {}
        self._tool_call_counts: dict[str, int] = {}

    def on_agent_start(self, agent_name: str, query: str) -> None:
        """Record start time and reset tool call counter for an agent invocation."""
        self._start_times[agent_name] = time.time()
        self._tool_call_counts[agent_name] = 0
        logger.info("Agent started", extra={
            "agent": agent_name,
            "query_preview": query[:200],
        })

    def on_tool_call(self, agent_name: str, tool_name: str, args: dict[str, object]) -> None:
        """Increment the tool call counter and log each tool invocation."""
        self._tool_call_counts[agent_name] = self._tool_call_counts.get(agent_name, 0) + 1
        logger.info("Tool called", extra={
            "agent": agent_name,
            "tool": tool_name,
            "call_number": self._tool_call_counts[agent_name],
        })

    def on_agent_end(self, agent_name: str, response_length: int) -> None:
        """Log elapsed time, tool call count, and response size when an agent finishes."""
        elapsed = time.time() - self._start_times.get(agent_name, time.time())
        tool_calls = self._tool_call_counts.get(agent_name, 0)
        logger.info("Agent completed", extra={
            "agent": agent_name,
            "duration_sec": round(elapsed, 2),
            "tool_calls": tool_calls,
            "response_chars": response_length,
        })

    def on_guardrail_violation(self, agent_name: str, violation_type: str, details: str) -> None:
        """Emit a warning log when an agent output breaches a guardrail rule."""
        logger.warning("Guardrail violation", extra={
            "agent": agent_name,
            "violation_type": violation_type,
            "details": details,
        })


callback_handler = AgentCallbackHandler()
