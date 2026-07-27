"""FastAPI dependency injection — DB sessions, agent runner."""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from src.agents.agent import root_agent

_session_service = InMemorySessionService()

_runner = Runner(
    agent=root_agent,
    app_name="primeev_factory",
    session_service=_session_service,
)

# Per-session message history: {session_id: [{"role", "content", "timestamp"}]}
_message_history: dict[str, list[dict]] = {}


def get_runner() -> Runner:
    """Return the shared ADK Runner instance for dependency injection."""
    return _runner


def get_session_service() -> InMemorySessionService:
    """Return the shared in-memory ADK session service."""
    return _session_service


def get_message_history() -> dict[str, list[dict]]:
    """Return the per-session message history dict (session_id → message list)."""
    return _message_history
