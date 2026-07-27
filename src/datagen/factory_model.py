"""PrimeEV Motors factory topology — defines the complete factory structure, BOMs, and production specs."""

from dataclasses import dataclass, field
from src.config.constants import (
    MACHINES,
    SENSOR_RANGES,
    STATIONS,
    STAGES,
    SUPPLIERS,
    VEHICLE_MODELS,
)


@dataclass
class SensorSpec:
    """Specification for a single sensor type on a machine."""

    sensor_type: str
    min_normal: float
    max_normal: float
    min_critical: float
    max_critical: float
    unit: str


@dataclass
class MachineSpec:
    """Full specification for a factory machine including its sensor suite."""

    machine_id: str
    station_id: str
    machine_type: str
    model: str
    criticality: str
    sensors: list[SensorSpec] = field(default_factory=list)
    maintenance_interval_hrs: float = 500.0
    expected_lifetime_hrs: float = 20000.0


@dataclass
class StationSpec:
    """Full specification for a production station including its machines."""

    station_id: str
    stage: str
    name: str
    position: int
    machines: list[MachineSpec] = field(default_factory=list)
    cycle_time_sec: float = 60.0
    target_fpy: float = 0.95


@dataclass
class Component:
    """A single BOM component consumed at a specific station."""

    part_number: str
    description: str
    category: str
    station_id: str
    supplier_id: str
    unit_cost: float


@dataclass
class VehicleModel:
    """Vehicle model definition with its associated BOM components."""

    model_id: str
    name: str
    year: int
    variant: str
    daily_target: int
    components: list[Component] = field(default_factory=list)


SENSOR_UNITS = {
    "TMP": "°C", "VIB": "mm/s", "PRS": "bar", "TRQ": "Nm",
    "RPM": "rpm", "PWR": "kW", "FLW": "L/min", "CUR": "A", "HUM": "%",
}


def _build_sensors(machine_type: str) -> list[SensorSpec]:
    """Build the list of SensorSpec objects for a given machine type."""
    ranges = SENSOR_RANGES.get(machine_type, {})
    return [
        SensorSpec(
            sensor_type=stype,
            min_normal=vals[0],
            max_normal=vals[1],
            min_critical=vals[2],
            max_critical=vals[3],
            unit=SENSOR_UNITS[stype],
        )
        for stype, vals in ranges.items()
    ]


def build_machines() -> dict[str, MachineSpec]:
    """Construct a mapping of machine_id to MachineSpec from the constants registry."""
    result = {}
    for machine_id, info in MACHINES.items():
        mtype = info["type"]
        maintenance_intervals = {
            "HYP": 400.0, "SRV": 500.0, "RBT": 800.0, "OVN": 600.0,
            "PMP": 350.0, "TST": 1000.0, "CNC": 450.0, "CNV": 1200.0,
        }
        lifetimes = {
            "HYP": 25000.0, "SRV": 30000.0, "RBT": 40000.0, "OVN": 20000.0,
            "PMP": 15000.0, "TST": 50000.0, "CNC": 20000.0, "CNV": 60000.0,
        }
        result[machine_id] = MachineSpec(
            machine_id=machine_id,
            station_id=info["station"],
            machine_type=mtype,
            model=info["model"],
            criticality=info["criticality"],
            sensors=_build_sensors(mtype),
            maintenance_interval_hrs=maintenance_intervals.get(mtype, 500.0),
            expected_lifetime_hrs=lifetimes.get(mtype, 20000.0),
        )
    return result


def build_stations() -> dict[str, StationSpec]:
    """Construct a mapping of station_id to StationSpec, populating each with its machines."""
    machines = build_machines()
    cycle_times = {
        "STP-01-PRS": 45.0, "STP-02-PRS": 45.0, "STP-03-TRM": 30.0,
        "WLD-01-UBD": 90.0, "WLD-02-SDP": 75.0, "WLD-03-RCL": 60.0,
        "PNT-01-ECT": 120.0, "PNT-02-PRM": 90.0, "PNT-03-CLR": 150.0,
        "ASM-01-PWR": 180.0, "ASM-02-INT": 240.0, "ASM-03-FNL": 120.0,
        "QAT-01-ALN": 60.0, "QAT-02-WLT": 45.0, "QAT-03-DYN": 300.0,
    }
    fpy_targets = {
        "STP-01-PRS": 0.97, "STP-02-PRS": 0.97, "STP-03-TRM": 0.98,
        "WLD-01-UBD": 0.95, "WLD-02-SDP": 0.96, "WLD-03-RCL": 0.96,
        "PNT-01-ECT": 0.94, "PNT-02-PRM": 0.93, "PNT-03-CLR": 0.95,
        "ASM-01-PWR": 0.97, "ASM-02-INT": 0.95, "ASM-03-FNL": 0.96,
        "QAT-01-ALN": 0.98, "QAT-02-WLT": 0.97, "QAT-03-DYN": 0.99,
    }
    result = {}
    for station_id, info in STATIONS.items():
        station_machines = [m for m in machines.values() if m.station_id == station_id]
        result[station_id] = StationSpec(
            station_id=station_id,
            stage=info["stage"],
            name=info["name"],
            position=info["position"],
            machines=station_machines,
            cycle_time_sec=cycle_times.get(station_id, 60.0),
            target_fpy=fpy_targets.get(station_id, 0.95),
        )
    return result


def build_vehicle_models() -> dict[str, VehicleModel]:
    """Construct a mapping of model_id to VehicleModel with full BOM definitions."""
    bom_definitions: dict[str, list[Component]] = {
        "PE-SD100": [
            Component("CHS-SD100-001", "Sedan chassis frame", "CHS", "STP-01-PRS", "SUP-MTL01", 2800.0),
            Component("CHS-SD100-002", "Sedan floor pan", "CHS", "STP-02-PRS", "SUP-MTL01", 1200.0),
            Component("EXT-SD100-010", "Sedan front door panel LH", "EXT", "STP-03-TRM", "SUP-MTL01", 340.0),
            Component("EXT-SD100-011", "Sedan front door panel RH", "EXT", "STP-03-TRM", "SUP-MTL01", 340.0),
            Component("EXT-SD100-012", "Sedan rear door panel LH", "EXT", "STP-03-TRM", "SUP-MTL01", 310.0),
            Component("EXT-SD100-013", "Sedan rear door panel RH", "EXT", "STP-03-TRM", "SUP-MTL01", 310.0),
            Component("EXT-SD100-014", "Sedan hood", "EXT", "STP-02-PRS", "SUP-MTL02", 580.0),
            Component("EXT-SD100-015", "Sedan trunk lid", "EXT", "STP-02-PRS", "SUP-MTL02", 420.0),
            Component("EXT-SD100-016", "Sedan roof panel", "EXT", "WLD-03-RCL", "SUP-MTL01", 650.0),
            Component("EXT-SD100-017", "Sedan fender LH", "EXT", "STP-03-TRM", "SUP-MTL02", 280.0),
            Component("EXT-SD100-018", "Sedan fender RH", "EXT", "STP-03-TRM", "SUP-MTL02", 280.0),
            Component("INT-SD100-020", "Sedan door trim LH", "INT", "ASM-02-INT", "SUP-PLY01", 185.0),
            Component("INT-SD100-021", "Sedan door trim RH", "INT", "ASM-02-INT", "SUP-PLY01", 185.0),
            Component("INT-SD100-022", "Sedan dashboard assembly", "INT", "ASM-02-INT", "SUP-PLY01", 950.0),
            Component("INT-SD100-023", "Sedan center console", "INT", "ASM-02-INT", "SUP-PLY01", 420.0),
            Component("INT-SD100-024", "Sedan headliner", "INT", "ASM-02-INT", "SUP-PLY01", 310.0),
            Component("INT-SD100-025", "Sedan seat assembly front LH", "INT", "ASM-02-INT", "SUP-PLY01", 680.0),
            Component("INT-SD100-026", "Sedan seat assembly front RH", "INT", "ASM-02-INT", "SUP-PLY01", 680.0),
            Component("PWR-SD100-030", "Sedan drive unit rear", "PWR", "ASM-01-PWR", "SUP-ELC01", 4200.0),
            Component("PWR-SD100-031", "Sedan drive unit front", "PWR", "ASM-01-PWR", "SUP-ELC01", 3800.0),
            Component("BAT-SD100-040", "Sedan battery pack 75kWh", "BAT", "ASM-01-PWR", "SUP-ELC01", 8500.0),
            Component("ELC-SD100-050", "Sedan main wiring harness", "ELC", "ASM-02-INT", "SUP-ELC01", 1200.0),
            Component("ELC-SD100-051", "Sedan HV junction box", "ELC", "ASM-01-PWR", "SUP-ELC01", 650.0),
            Component("SUS-SD100-060", "Sedan front suspension assembly", "SUS", "ASM-03-FNL", "SUP-MTL01", 920.0),
            Component("SUS-SD100-061", "Sedan rear suspension assembly", "SUS", "ASM-03-FNL", "SUP-MTL01", 880.0),
            Component("BRK-SD100-070", "Sedan brake caliper set", "BRK", "ASM-03-FNL", "SUP-MTL01", 560.0),
            Component("SEL-SD100-080", "Sedan windshield sealant kit", "SEL", "ASM-03-FNL", "SUP-CHM01", 45.0),
            Component("SEL-SD100-081", "Sedan body seam sealer", "SEL", "PNT-01-ECT", "SUP-CHM01", 32.0),
            Component("RAW-STL-001", "Steel sheet 1.2mm CR", "RAW", "STP-01-PRS", "SUP-MTL01", 85.0),
            Component("RAW-STL-002", "Steel sheet 0.8mm CR", "RAW", "STP-02-PRS", "SUP-MTL01", 72.0),
            Component("RAW-ALU-001", "Aluminum sheet 1.5mm 6016-T4", "RAW", "STP-01-PRS", "SUP-MTL02", 120.0),
        ],
        "PE-SV200": [
            Component("CHS-SV200-001", "SUV chassis frame", "CHS", "STP-01-PRS", "SUP-MTL01", 3400.0),
            Component("CHS-SV200-002", "SUV floor pan", "CHS", "STP-02-PRS", "SUP-MTL01", 1500.0),
            Component("EXT-SV200-010", "SUV front door panel LH", "EXT", "STP-03-TRM", "SUP-MTL01", 380.0),
            Component("EXT-SV200-011", "SUV front door panel RH", "EXT", "STP-03-TRM", "SUP-MTL01", 380.0),
            Component("EXT-SV200-012", "SUV rear door panel LH", "EXT", "STP-03-TRM", "SUP-MTL01", 360.0),
            Component("EXT-SV200-013", "SUV rear door panel RH", "EXT", "STP-03-TRM", "SUP-MTL01", 360.0),
            Component("EXT-SV200-014", "SUV hood", "EXT", "STP-02-PRS", "SUP-MTL02", 640.0),
            Component("EXT-SV200-015", "SUV tailgate", "EXT", "STP-02-PRS", "SUP-MTL02", 720.0),
            Component("EXT-SV200-016", "SUV roof panel", "EXT", "WLD-03-RCL", "SUP-MTL01", 780.0),
            Component("INT-SV200-020", "SUV door trim LH", "INT", "ASM-02-INT", "SUP-PLY01", 210.0),
            Component("INT-SV200-021", "SUV door trim RH", "INT", "ASM-02-INT", "SUP-PLY01", 210.0),
            Component("INT-SV200-022", "SUV dashboard assembly", "INT", "ASM-02-INT", "SUP-PLY01", 1100.0),
            Component("INT-SV200-023", "SUV center console", "INT", "ASM-02-INT", "SUP-PLY01", 480.0),
            Component("INT-SV200-025", "SUV seat assembly front LH", "INT", "ASM-02-INT", "SUP-PLY01", 750.0),
            Component("INT-SV200-026", "SUV seat assembly front RH", "INT", "ASM-02-INT", "SUP-PLY01", 750.0),
            Component("INT-SV200-027", "SUV third-row seat assembly", "INT", "ASM-02-INT", "SUP-PLY01", 620.0),
            Component("PWR-SV200-030", "SUV drive unit rear", "PWR", "ASM-01-PWR", "SUP-ELC01", 4800.0),
            Component("PWR-SV200-031", "SUV drive unit front", "PWR", "ASM-01-PWR", "SUP-ELC01", 4200.0),
            Component("BAT-SV200-040", "SUV battery pack 100kWh", "BAT", "ASM-01-PWR", "SUP-ELC01", 11200.0),
            Component("ELC-SV200-050", "SUV main wiring harness", "ELC", "ASM-02-INT", "SUP-ELC01", 1400.0),
            Component("SUS-SV200-060", "SUV front suspension assembly", "SUS", "ASM-03-FNL", "SUP-MTL01", 1050.0),
            Component("SUS-SV200-061", "SUV rear suspension assembly", "SUS", "ASM-03-FNL", "SUP-MTL01", 1020.0),
            Component("BRK-SV200-070", "SUV brake caliper set", "BRK", "ASM-03-FNL", "SUP-MTL01", 640.0),
            Component("RAW-STL-001", "Steel sheet 1.2mm CR", "RAW", "STP-01-PRS", "SUP-MTL01", 85.0),
            Component("RAW-STL-003", "Steel sheet 1.5mm CR", "RAW", "STP-01-PRS", "SUP-MTL01", 95.0),
            Component("RAW-ALU-001", "Aluminum sheet 1.5mm 6016-T4", "RAW", "STP-01-PRS", "SUP-MTL02", 120.0),
        ],
        "PE-CP300": [
            Component("CHS-CP300-001", "Compact chassis frame", "CHS", "STP-01-PRS", "SUP-MTL01", 2200.0),
            Component("CHS-CP300-002", "Compact floor pan", "CHS", "STP-02-PRS", "SUP-MTL01", 950.0),
            Component("EXT-CP300-010", "Compact front door panel LH", "EXT", "STP-03-TRM", "SUP-MTL01", 290.0),
            Component("EXT-CP300-011", "Compact front door panel RH", "EXT", "STP-03-TRM", "SUP-MTL01", 290.0),
            Component("EXT-CP300-012", "Compact rear door panel LH", "EXT", "STP-03-TRM", "SUP-MTL01", 270.0),
            Component("EXT-CP300-013", "Compact rear door panel RH", "EXT", "STP-03-TRM", "SUP-MTL01", 270.0),
            Component("EXT-CP300-014", "Compact hood", "EXT", "STP-02-PRS", "SUP-MTL02", 480.0),
            Component("EXT-CP300-015", "Compact hatchback", "EXT", "STP-02-PRS", "SUP-MTL02", 380.0),
            Component("EXT-CP300-016", "Compact roof panel", "EXT", "WLD-03-RCL", "SUP-MTL01", 520.0),
            Component("INT-CP300-020", "Compact door trim LH", "INT", "ASM-02-INT", "SUP-PLY01", 155.0),
            Component("INT-CP300-021", "Compact door trim RH", "INT", "ASM-02-INT", "SUP-PLY01", 155.0),
            Component("INT-CP300-022", "Compact dashboard assembly", "INT", "ASM-02-INT", "SUP-PLY01", 780.0),
            Component("INT-CP300-025", "Compact seat assembly front LH", "INT", "ASM-02-INT", "SUP-PLY01", 550.0),
            Component("INT-CP300-026", "Compact seat assembly front RH", "INT", "ASM-02-INT", "SUP-PLY01", 550.0),
            Component("PWR-CP300-030", "Compact drive unit rear", "PWR", "ASM-01-PWR", "SUP-ELC01", 3200.0),
            Component("BAT-CP300-040", "Compact battery pack 55kWh", "BAT", "ASM-01-PWR", "SUP-ELC01", 6400.0),
            Component("ELC-CP300-050", "Compact main wiring harness", "ELC", "ASM-02-INT", "SUP-ELC01", 980.0),
            Component("SUS-CP300-060", "Compact front suspension assembly", "SUS", "ASM-03-FNL", "SUP-MTL01", 780.0),
            Component("SUS-CP300-061", "Compact rear suspension assembly", "SUS", "ASM-03-FNL", "SUP-MTL01", 720.0),
            Component("BRK-CP300-070", "Compact brake caliper set", "BRK", "ASM-03-FNL", "SUP-MTL01", 480.0),
            Component("RAW-STL-001", "Steel sheet 1.2mm CR", "RAW", "STP-01-PRS", "SUP-MTL01", 85.0),
            Component("RAW-ALU-002", "Aluminum extrusion 6063-T5", "RAW", "STP-01-PRS", "SUP-MTL02", 95.0),
        ],
    }

    daily_targets = {"PE-SD100": 30, "PE-SV200": 25, "PE-CP300": 25}

    result = {}
    for model_id, info in VEHICLE_MODELS.items():
        result[model_id] = VehicleModel(
            model_id=model_id,
            name=info["name"],
            year=info["year"],
            variant=info["variant"],
            daily_target=daily_targets[model_id],
            components=bom_definitions.get(model_id, []),
        )
    return result


# Pre-built factory objects for easy import
FACTORY_MACHINES = build_machines()
FACTORY_STATIONS = build_stations()
FACTORY_VEHICLE_MODELS = build_vehicle_models()

ALL_MACHINE_IDS = list(FACTORY_MACHINES.keys())
ALL_STATION_IDS = list(FACTORY_STATIONS.keys())
ALL_MODEL_IDS = list(FACTORY_VEHICLE_MODELS.keys())
STAGE_ORDER = ["STP", "WLD", "PNT", "ASM", "QAT"]
