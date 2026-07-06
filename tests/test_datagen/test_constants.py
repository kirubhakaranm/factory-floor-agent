"""Verify factory domain constants are consistent."""

from src.config.constants import (
    MACHINES,
    STATIONS,
    STATION_DEFECTS,
    VEHICLE_MODELS,
    generate_vin,
    generate_work_order_id,
)


def test_all_stations_have_defect_types() -> None:
    for station_id in STATIONS:
        assert station_id in STATION_DEFECTS, f"Missing defect types for {station_id}"
        assert len(STATION_DEFECTS[station_id]) >= 3


def test_all_machines_reference_valid_stations() -> None:
    for machine_id, machine in MACHINES.items():
        station = machine["station"]
        assert station in STATIONS, f"Machine {machine_id} references unknown station {station}"


def test_vin_generation() -> None:
    vin = generate_vin("SD100", 2026, 4521)
    assert vin == "PEF-SD100-26-004521"


def test_work_order_id_generation() -> None:
    wo_id = generate_work_order_id(2026, 6, 142)
    assert wo_id == "WO-2606-00142"


def test_vehicle_models_exist() -> None:
    assert len(VEHICLE_MODELS) == 3
    assert "PE-SD100" in VEHICLE_MODELS
    assert "PE-SV200" in VEHICLE_MODELS
    assert "PE-CP300" in VEHICLE_MODELS
