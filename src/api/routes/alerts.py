"""Alerts endpoint — recent equipment failures as active alerts."""

import asyncio
from datetime import datetime

from fastapi import APIRouter

from src.api.schemas import Alert, AlertList

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts", response_model=AlertList)
async def get_alerts(
    station_id: str | None = None,
    severity: str | None = None,
    days_back: int = 7,
) -> AlertList:
    """Get recent equipment failures as active alerts, filtered by station or severity.

    Backed by the equipment_failures table (Postgres). Returns the most recent
    50 failures within the requested time window as Alert objects.
    """
    loop = asyncio.get_event_loop()
    try:
        from src.db.postgres import queries as pg
        failures = await loop.run_in_executor(
            None, pg.sync_get_recent_failures, station_id, severity, days_back, 50
        )
    except Exception:
        return AlertList(alerts=[], total=0)

    alerts = []
    for f in failures:
        try:
            ts = datetime.fromisoformat(f["failure_start"])
        except (KeyError, ValueError, TypeError):
            ts = datetime.now()

        alerts.append(Alert(
            alert_id=f.get("failure_id", ""),
            machine_id=f.get("machine_id", ""),
            station_id=f.get("station_id", ""),
            alert_type=f.get("failure_mode") or "equipment_failure",
            severity=f.get("severity") or "unknown",
            message=(
                f.get("corrective_action")
                or f.get("failure_mode")
                or "Equipment failure detected"
            ),
            timestamp=ts,
            acknowledged=False,
        ))

    return AlertList(alerts=alerts, total=len(alerts))
