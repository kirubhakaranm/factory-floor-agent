"""Pydantic request/response models for all API routes."""

from datetime import datetime
from pydantic import BaseModel, Field


# ─── Chat ──────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, description="Existing session ID to continue")


class ChatEvent(BaseModel):
    """SSE event sent during chat streaming."""
    event_type: str = Field(..., description="token | tool_call | tool_result | done | error")
    data: str = Field(default="")
    agent_name: str | None = None
    tool_name: str | None = None


# ─── Sessions ──────────────────────────────────────────────────────────────────


class SessionCreate(BaseModel):
    pass


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    message_count: int = 0


class SessionMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class SessionDetail(BaseModel):
    session_id: str
    created_at: datetime
    messages: list[SessionMessage] = []


# ─── Factory ───────────────────────────────────────────────────────────────────


class StationStatus(BaseModel):
    station_id: str
    name: str
    stage: str
    status: str = "running"  # running | degraded | down | idle
    machine_count: int = 0
    active_alerts: int = 0


class FactoryStatus(BaseModel):
    timestamp: datetime
    stations: list[StationStatus]
    total_machines: int
    active_alerts: int
    shift: str


class MachineInfo(BaseModel):
    machine_id: str
    station_id: str
    machine_type: str
    model: str
    criticality: str
    status: str = "active"


class SensorReading(BaseModel):
    machine_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime | None = None


# ─── Alerts ────────────────────────────────────────────────────────────────────


class Alert(BaseModel):
    alert_id: str
    machine_id: str
    station_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool = False


class AlertList(BaseModel):
    alerts: list[Alert]
    total: int


# ─── Health ────────────────────────────────────────────────────────────────────


class HealthCheck(BaseModel):
    status: str
    service: str
    version: str = "0.1.0"
    checks: dict[str, str] = {}
