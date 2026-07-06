"""Kafka topic definitions and message schemas."""

from dataclasses import dataclass, asdict
from datetime import datetime
import json


# ─── Topic Names ───────────────────────────────────────────────────────────────

TOPIC_SENSORS_RAW = "factory.sensors.raw"
TOPIC_ALERTS_NEW = "factory.alerts.new"
TOPIC_PRODUCTION_EVENTS = "factory.production.events"

ALL_TOPICS = [TOPIC_SENSORS_RAW, TOPIC_ALERTS_NEW, TOPIC_PRODUCTION_EVENTS]


# ─── Message Schemas ───────────────────────────────────────────────────────────


@dataclass
class SensorMessage:
    machine_id: str
    station_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: str  # ISO format

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> "SensorMessage":
        return cls(**json.loads(data))


@dataclass
class AlertMessage:
    alert_id: str
    machine_id: str
    station_id: str
    alert_type: str
    severity: str
    sensor_type: str
    sensor_value: float
    threshold: float
    message: str
    timestamp: str

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> "AlertMessage":
        return cls(**json.loads(data))


@dataclass
class ProductionEventMessage:
    event_type: str  # batch_start, batch_end, station_status, shift_change
    station_id: str
    batch_id: str | None = None
    model_id: str | None = None
    operator_id: str | None = None
    status: str | None = None  # running, idle, down, changeover
    timestamp: str = ""

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> "ProductionEventMessage":
        return cls(**json.loads(data))
