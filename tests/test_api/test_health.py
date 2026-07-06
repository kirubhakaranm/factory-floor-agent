"""Smoke tests for API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "primeev-factory-agent"
    assert "agent" in data["checks"]


def test_factory_status() -> None:
    response = client.get("/api/factory/status")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stations"]) == 15
    assert data["total_machines"] >= 25
    assert data["shift"] in ("Day", "Swing", "Night")


def test_station_machines() -> None:
    response = client.get("/api/factory/stations/STP-01-PRS/machines")
    assert response.status_code == 200
    machines = response.json()
    assert len(machines) >= 1
    assert machines[0]["station_id"] == "STP-01-PRS"


def test_alerts_empty() -> None:
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_sessions_list() -> None:
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_session() -> None:
    response = client.post("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data


def test_metrics_endpoint() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
