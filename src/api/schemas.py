"""Pydantic request/response models for all API routes."""

from datetime import datetime
from pydantic import BaseModel, Field


# ─── Chat ──────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Request body for the POST /api/chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, description="Existing session ID to continue")
    response_mode: str = Field(default="detailed", pattern="^(detailed|concise|summarized)$")


class ReformatRequest(BaseModel):
    """Request body for reformatting an existing agent response."""

    original_text: str = Field(..., min_length=1)
    target_mode: str = Field(..., pattern="^(detailed|concise|summarized)$")


class ChatEvent(BaseModel):
    """SSE event sent during chat streaming."""
    event_type: str = Field(..., description="token | tool_call | tool_result | done | error")
    data: str = Field(default="")
    agent_name: str | None = None
    tool_name: str | None = None


# ─── Sessions ──────────────────────────────────────────────────────────────────


class SessionCreate(BaseModel):
    """Request body for creating a new chat session (currently empty)."""

    pass


class SessionInfo(BaseModel):
    """Summary of a chat session returned by the list-sessions endpoint."""

    session_id: str
    created_at: datetime
    message_count: int = 0


class SessionMessage(BaseModel):
    """A single message within a session's conversation history."""

    role: str
    content: str
    timestamp: datetime


class SessionDetail(BaseModel):
    """Full detail for a chat session including its complete message history."""

    session_id: str
    created_at: datetime
    messages: list[SessionMessage] = []


# ─── Factory ───────────────────────────────────────────────────────────────────


class StationStatus(BaseModel):
    """Live status snapshot for a single production station."""

    station_id: str
    name: str
    stage: str
    status: str = "running"  # running | degraded | down | idle
    machine_count: int = 0
    active_alerts: int = 0
    oee: float | None = None


class FactoryStatus(BaseModel):
    """Aggregated status of all stations returned by the factory-status endpoint."""

    timestamp: datetime
    stations: list[StationStatus]
    total_machines: int
    active_alerts: int
    shift: str


class MachineInfo(BaseModel):
    """Static metadata for a single machine (type, model, criticality)."""

    machine_id: str
    station_id: str
    machine_type: str
    model: str
    criticality: str
    status: str = "active"


class SensorReading(BaseModel):
    """A single sensor reading returned from the live sensor endpoint."""

    machine_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime | None = None


# ─── Alerts ────────────────────────────────────────────────────────────────────


class Alert(BaseModel):
    """An active equipment alert surfaced from recent failure records."""

    alert_id: str
    machine_id: str
    station_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool = False


class AlertList(BaseModel):
    """Paginated list of active alerts with a total count."""

    alerts: list[Alert]
    total: int


# ─── Health ────────────────────────────────────────────────────────────────────


class HealthCheck(BaseModel):
    """Health check response with per-dependency status strings."""

    status: str
    service: str
    version: str = "0.1.0"
    checks: dict[str, str] = {}
