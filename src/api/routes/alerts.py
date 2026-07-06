"""Alerts endpoint — active alerts and alert history."""

from fastapi import APIRouter

from src.api.schemas import Alert, AlertList

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts", response_model=AlertList)
async def get_alerts(
    station_id: str | None = None,
    severity: str | None = None,
) -> AlertList:
    """Get active alerts, optionally filtered by station or severity.

    Alert data will be populated from Kafka consumer in Phase 7.
    """
    return AlertList(alerts=[], total=0)
