"""Smoke tests for API health, factory, alerts, sessions, and metrics endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """GET /api/health returns 200 with status and per-dependency check keys."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "primeev-factory-agent"
    assert "agent" in data["checks"]


def test_factory_status() -> None:
    """GET /api/factory/status returns all 15 stations with machine count and shift."""
    response = client.get("/api/factory/status")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stations"]) == 15
    assert data["total_machines"] >= 25
    assert data["shift"] in ("Day", "Swing", "Night")


def test_station_machines() -> None:
    """GET /api/factory/stations/{id}/machines returns machines belonging to that station."""
    response = client.get("/api/factory/stations/STP-01-PRS/machines")
    assert response.status_code == 200
    machines = response.json()
    assert len(machines) >= 1
    assert machines[0]["station_id"] == "STP-01-PRS"


def test_alerts_empty() -> None:
    """GET /api/alerts returns an AlertList with total=0 when DB is unavailable."""
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_sessions_list() -> None:
    """GET /api/sessions returns a list (may be empty when DB is unavailable)."""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_session() -> None:
    """POST /api/sessions returns a response containing a session_id field."""
    response = client.post("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data


def test_metrics_endpoint() -> None:
    """GET /metrics returns 200 (Prometheus scrape endpoint)."""
    response = client.get("/metrics")
    assert response.status_code == 200
