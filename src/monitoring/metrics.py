"""Prometheus metrics for agent and API monitoring."""

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import APIRouter

router = APIRouter(tags=["monitoring"])

# Agent metrics
AGENT_REQUEST_DURATION = Histogram(
    "agent_request_duration_seconds",
    "Time spent processing agent requests",
    ["agent_name"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

AGENT_TOOL_CALLS = Counter(
    "agent_tool_calls_total",
    "Total tool calls made by agents",
    ["agent_name", "tool_name"],
)

AGENT_ERRORS = Counter(
    "agent_errors_total",
    "Total agent errors",
    ["agent_name", "error_type"],
)

AGENT_REQUESTS = Counter(
    "agent_requests_total",
    "Total agent requests",
    ["agent_name"],
)

# API metrics
API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "Time spent processing API requests",
    ["method", "endpoint", "status"],
)


@router.get("/metrics")
async def metrics() -> bytes:
    """Prometheus metrics endpoint."""
    return generate_latest()
