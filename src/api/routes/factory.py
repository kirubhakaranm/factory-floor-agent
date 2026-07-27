"""Factory status endpoints — stations, machines, sensors, VIN traceability."""

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.api.schemas import FactoryStatus, MachineInfo, StationStatus
from src.datagen.factory_model import FACTORY_MACHINES, FACTORY_STATIONS

router = APIRouter(prefix="/api/factory", tags=["factory"])


def _get_shift() -> str:
    """Return the current shift name (Day/Swing/Night) based on the wall-clock hour."""
    hour = datetime.now().hour
    if 6 <= hour < 14:
        return "Day"
    elif 14 <= hour < 22:
        return "Swing"
    return "Night"


@router.get("/status", response_model=FactoryStatus)
async def get_factory_status() -> FactoryStatus:
    """Get current status of all stations with live OEE and alert counts."""
    loop = asyncio.get_event_loop()

    # Alert counts from recent failures (last 24 h)
    alert_counts: dict[str, int] = {}
    total_alerts = 0
    try:
        from src.db.postgres import queries as pg
        failures = await loop.run_in_executor(
            None, pg.sync_get_recent_failures, None, None, 1, 500
        )
        for f in failures:
            sid = f.get("station_id", "")
            alert_counts[sid] = alert_counts.get(sid, 0) + 1
            total_alerts += 1
    except Exception:
        pass  # DB unavailable — degrade gracefully

    # Latest OEE per station from ClickHouse (single query)
    oee_by_station: dict[str, float] = {}
    try:
        from src.db.clickhouse import queries as ch
        rows = await loop.run_in_executor(None, ch.get_all_stations_latest_oee)
        for row in rows:
            oee_by_station[row["station_id"]] = round(float(row["latest_oee"]), 3)
    except Exception:
        pass  # ClickHouse unavailable — degrade gracefully

    stations = []
    for station_id, station in FACTORY_STATIONS.items():
        oee = oee_by_station.get(station_id)
        # Derive status from OEE: <0.40 = down, <0.60 = degraded, else running
        if oee is not None:
            if oee < 0.40:
                status = "down"
            elif oee < 0.60:
                status = "degraded"
            else:
                status = "running"
        else:
            status = "running"

        stations.append(StationStatus(
            station_id=station_id,
            name=station.name,
            stage=station.stage,
            status=status,
            machine_count=len(station.machines),
            active_alerts=alert_counts.get(station_id, 0),
            oee=oee,
        ))

    return FactoryStatus(
        timestamp=datetime.now(),
        stations=stations,
        total_machines=len(FACTORY_MACHINES),
        active_alerts=total_alerts,
        shift=_get_shift(),
    )


@router.get("/stations/{station_id}/machines", response_model=list[MachineInfo])
async def get_station_machines(station_id: str) -> list[MachineInfo]:
    """Get all machines at a station."""
    station = FACTORY_STATIONS.get(station_id)
    if not station:
        return []

    return [
        MachineInfo(
            machine_id=m.machine_id,
            station_id=m.station_id,
            machine_type=m.machine_type,
            model=m.model,
            criticality=m.criticality,
        )
        for m in station.machines
    ]


@router.get("/machines/{machine_id}", response_model=MachineInfo)
async def get_machine_info(machine_id: str) -> MachineInfo:
    """Get details for a specific machine."""
    machine = FACTORY_MACHINES.get(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    return MachineInfo(
        machine_id=machine.machine_id,
        station_id=machine.station_id,
        machine_type=machine.machine_type,
        model=machine.model,
        criticality=machine.criticality,
    )


@router.get("/stations/{station_id}/sensors")
async def get_station_sensors(station_id: str) -> list[dict]:
    """Get the latest sensor reading per machine/sensor_type at a station from ClickHouse."""
    loop = asyncio.get_event_loop()
    try:
        from src.db.clickhouse import queries as ch
        return await loop.run_in_executor(None, ch.get_current_readings, station_id)
    except Exception:
        return []


@router.get("/vin/{vin_id}")
async def get_vin_history(vin_id: str) -> dict:
    """Get full production trail for a VIN: registry, batch, quality context, finished goods."""
    loop = asyncio.get_event_loop()
    try:
        from src.db.postgres import queries as pg
        result = await loop.run_in_executor(None, pg.sync_get_vin_history, vin_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
