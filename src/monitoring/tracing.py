"""Agent execution tracing — captures tool call sequences for debugging and evals."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolCallTrace:
    tool_name: str
    args: dict
    result_preview: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0


@dataclass
class AgentTrace:
    session_id: str
    agent_name: str
    query: str
    tool_calls: list[ToolCallTrace] = field(default_factory=list)
    response: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    total_duration_ms: float = 0.0

    def add_tool_call(self, tool_name: str, args: dict, result: str, duration_ms: float) -> None:
        self.tool_calls.append(ToolCallTrace(
            tool_name=tool_name,
            args=args,
            result_preview=result[:200],
            duration_ms=duration_ms,
        ))

    def complete(self, response: str) -> None:
        self.response = response
        self.completed_at = datetime.now()
        self.total_duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "query": self.query,
            "tool_calls": [
                {"tool": tc.tool_name, "args": tc.args, "duration_ms": tc.duration_ms}
                for tc in self.tool_calls
            ],
            "response_preview": self.response[:500],
            "total_duration_ms": self.total_duration_ms,
            "tool_call_count": len(self.tool_calls),
        }
