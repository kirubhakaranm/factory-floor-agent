"""Factory status endpoints — stations, machines, sensors."""

from datetime import datetime

from fastapi import APIRouter

from src.api.schemas import FactoryStatus, MachineInfo, StationStatus
from src.datagen.factory_model import FACTORY_MACHINES, FACTORY_STATIONS

router = APIRouter(prefix="/api/factory", tags=["factory"])


@router.get("/status", response_model=FactoryStatus)
async def get_factory_status() -> FactoryStatus:
    """Get current status of all stations."""
    stations = []
    for station_id, station in FACTORY_STATIONS.items():
        stations.append(StationStatus(
            station_id=station_id,
            name=station.name,
            stage=station.stage,
            status="running",
            machine_count=len(station.machines),
            active_alerts=0,
        ))

    hour = datetime.now().hour
    if 6 <= hour < 14:
        shift = "Day"
    elif 14 <= hour < 22:
        shift = "Swing"
    else:
        shift = "Night"

    return FactoryStatus(
        timestamp=datetime.now(),
        stations=stations,
        total_machines=len(FACTORY_MACHINES),
        active_alerts=0,
        shift=shift,
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
async def get_machine_info(machine_id: str) -> MachineInfo | dict:
    """Get details for a specific machine."""
    machine = FACTORY_MACHINES.get(machine_id)
    if not machine:
        return {"error": f"Machine {machine_id} not found"}

    return MachineInfo(
        machine_id=machine.machine_id,
        station_id=machine.station_id,
        machine_type=machine.machine_type,
        model=machine.model,
        criticality=machine.criticality,
    )
