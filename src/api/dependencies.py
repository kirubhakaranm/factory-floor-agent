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


def get_runner() -> Runner:
    return _runner


def get_session_service() -> InMemorySessionService:
    return _session_service
