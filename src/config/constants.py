"""PrimeEV Motors factory domain constants — naming conventions, station IDs, sensor ranges, defect types."""

from dataclasses import dataclass, field

# ─── Company ───────────────────────────────────────────────────────────────────

COMPANY_NAME = "PrimeEV Motors"
COMPANY_PREFIX = "PE"
PLANT_CODE = "PE-FRE"

# ─── Stages ────────────────────────────────────────────────────────────────────

STAGES = {
    "STP": "Stamping",
    "WLD": "Welding",
    "PNT": "Paint",
    "ASM": "Assembly",
    "QAT": "Quality & Test",
}

# ─── Stations ──────────────────────────────────────────────────────────────────

STATIONS = {
    "STP-01-PRS": {"stage": "STP", "name": "Press 1", "position": 1},
    "STP-02-PRS": {"stage": "STP", "name": "Press 2", "position": 2},
    "STP-03-TRM": {"stage": "STP", "name": "Trim/Pierce", "position": 3},
    "WLD-01-UBD": {"stage": "WLD", "name": "Underbody", "position": 1},
    "WLD-02-SDP": {"stage": "WLD", "name": "Side Panel", "position": 2},
    "WLD-03-RCL": {"stage": "WLD", "name": "Roof/Closure", "position": 3},
    "PNT-01-ECT": {"stage": "PNT", "name": "E-Coat", "position": 1},
    "PNT-02-PRM": {"stage": "PNT", "name": "Prime/Base", "position": 2},
    "PNT-03-CLR": {"stage": "PNT", "name": "Clear/Cure", "position": 3},
    "ASM-01-PWR": {"stage": "ASM", "name": "Powertrain Mount", "position": 1},
    "ASM-02-INT": {"stage": "ASM", "name": "Interior/Wiring", "position": 2},
    "ASM-03-FNL": {"stage": "ASM", "name": "Final Fit", "position": 3},
    "QAT-01-ALN": {"stage": "QAT", "name": "Alignment Check", "position": 1},
    "QAT-02-WLT": {"stage": "QAT", "name": "Water Leak Test", "position": 2},
    "QAT-03-DYN": {"stage": "QAT", "name": "Dyno/Road Test", "position": 3},
}

# ─── Machines ──────────────────────────────────────────────────────────────────

MACHINE_TYPES = {
    "HYP": "Hydraulic Press",
    "SRV": "Servo Press",
    "RBT": "Robot",
    "CNC": "CNC Machine",
    "OVN": "Oven/Curing",
    "TST": "Test Equipment",
    "CNV": "Conveyor",
    "PMP": "Pump Unit",
}

MACHINES = {
    # Stamping
    "STP-01-PRS-HYP01": {"station": "STP-01-PRS", "type": "HYP", "model": "Schuler TwinServo 2800", "criticality": "A"},
    "STP-01-PRS-HYP02": {"station": "STP-01-PRS", "type": "HYP", "model": "Schuler TwinServo 2800", "criticality": "B"},
    "STP-02-PRS-SRV01": {"station": "STP-02-PRS", "type": "SRV", "model": "Komatsu H2F 1600", "criticality": "A"},
    "STP-03-TRM-SRV01": {"station": "STP-03-TRM", "type": "SRV", "model": "Komatsu H1F 800", "criticality": "A"},
    "STP-03-TRM-SRV02": {"station": "STP-03-TRM", "type": "SRV", "model": "Komatsu H1F 800", "criticality": "B"},
    # Welding
    "WLD-01-UBD-RBT01": {"station": "WLD-01-UBD", "type": "RBT", "model": "Fanuc R-2000iC/210F", "criticality": "A"},
    "WLD-01-UBD-RBT02": {"station": "WLD-01-UBD", "type": "RBT", "model": "Fanuc R-2000iC/210F", "criticality": "A"},
    "WLD-02-SDP-RBT01": {"station": "WLD-02-SDP", "type": "RBT", "model": "Fanuc R-2000iC/165F", "criticality": "A"},
    "WLD-02-SDP-RBT02": {"station": "WLD-02-SDP", "type": "RBT", "model": "Fanuc R-2000iC/165F", "criticality": "B"},
    "WLD-03-RCL-RBT01": {"station": "WLD-03-RCL", "type": "RBT", "model": "Fanuc R-1000iA/100F", "criticality": "A"},
    # Paint
    "PNT-01-ECT-PMP01": {"station": "PNT-01-ECT", "type": "PMP", "model": "Graco E-Flo DC 2200", "criticality": "A"},
    "PNT-01-ECT-PMP02": {"station": "PNT-01-ECT", "type": "PMP", "model": "Graco E-Flo DC 2200", "criticality": "B"},
    "PNT-02-PRM-RBT01": {"station": "PNT-02-PRM", "type": "RBT", "model": "ABB IRB 5500 FlexPainter", "criticality": "A"},
    "PNT-02-PRM-RBT02": {"station": "PNT-02-PRM", "type": "RBT", "model": "ABB IRB 5500 FlexPainter", "criticality": "A"},
    "PNT-03-CLR-OVN01": {"station": "PNT-03-CLR", "type": "OVN", "model": "Dürr EcoInCure 4.0", "criticality": "A"},
    "PNT-03-CLR-RBT01": {"station": "PNT-03-CLR", "type": "RBT", "model": "ABB IRB 5500 FlexPainter", "criticality": "A"},
    # Assembly
    "ASM-01-PWR-RBT01": {"station": "ASM-01-PWR", "type": "RBT", "model": "KUKA KR 1000 Titan", "criticality": "A"},
    "ASM-01-PWR-RBT02": {"station": "ASM-01-PWR", "type": "RBT", "model": "KUKA KR 360", "criticality": "B"},
    "ASM-02-INT-RBT01": {"station": "ASM-02-INT", "type": "RBT", "model": "Universal Robots UR10e", "criticality": "B"},
    "ASM-03-FNL-RBT01": {"station": "ASM-03-FNL", "type": "RBT", "model": "Fanuc CR-35iA", "criticality": "A"},
    # Quality & Test
    "QAT-01-ALN-TST01": {"station": "QAT-01-ALN", "type": "TST", "model": "Hunter WA Series", "criticality": "A"},
    "QAT-02-WLT-TST01": {"station": "QAT-02-WLT", "type": "TST", "model": "Ingersoll Rand Leak Tester LT-500", "criticality": "A"},
    "QAT-03-DYN-TST01": {"station": "QAT-03-DYN", "type": "TST", "model": "Meidensha DYNAS3 LI 200", "criticality": "A"},
    "QAT-03-DYN-TST02": {"station": "QAT-03-DYN", "type": "TST", "model": "Meidensha DYNAS3 LI 200", "criticality": "B"},
    # Conveyors (shared)
    "STP-CNV01": {"station": "STP-01-PRS", "type": "CNV", "model": "Daifuku Electrified Monorail", "criticality": "B"},
    "WLD-CNV01": {"station": "WLD-01-UBD", "type": "CNV", "model": "Daifuku Electrified Monorail", "criticality": "B"},
    "PNT-CNV01": {"station": "PNT-01-ECT", "type": "CNV", "model": "Daifuku Electrified Monorail", "criticality": "B"},
    "ASM-CNV01": {"station": "ASM-01-PWR", "type": "CNV", "model": "Daifuku Electrified Monorail", "criticality": "B"},
    "QAT-CNV01": {"station": "QAT-01-ALN", "type": "CNV", "model": "Daifuku Electrified Monorail", "criticality": "C"},
}

# ─── Vehicle Models ────────────────────────────────────────────────────────────

VEHICLE_MODELS = {
    "PE-SD100": {"name": "PrimeEV Sedan 100", "year": 2026, "variant": "sedan"},
    "PE-SV200": {"name": "PrimeEV SUV 200", "year": 2026, "variant": "suv"},
    "PE-CP300": {"name": "PrimeEV Compact 300", "year": 2026, "variant": "compact"},
}

COMPONENT_CATEGORIES = {
    "CHS": "Chassis / Body Structure",
    "EXT": "Exterior Panel",
    "INT": "Interior Trim",
    "PWR": "Powertrain",
    "ELC": "Electrical",
    "BAT": "Battery",
    "SUS": "Suspension",
    "BRK": "Brake",
    "FST": "Fastener",
    "SEL": "Sealant / Adhesive",
    "RAW": "Raw Material",
}

# ─── Suppliers ─────────────────────────────────────────────────────────────────

SUPPLIERS = {
    "SUP-MTL01": {"name": "SteelWorks Inc.", "category": "metals"},
    "SUP-MTL02": {"name": "AluForm Global", "category": "aluminum"},
    "SUP-PLY01": {"name": "PolyTech Materials", "category": "plastics/rubber"},
    "SUP-ELC01": {"name": "VoltCell Energy", "category": "battery/wiring"},
    "SUP-CHM01": {"name": "CoatChem Solutions", "category": "paint/coatings"},
}

# ─── Sensor Types ──────────────────────────────────────────────────────────────

SENSOR_TYPES = {
    "TMP": {"name": "Temperature", "unit": "°C"},
    "VIB": {"name": "Vibration", "unit": "mm/s"},
    "PRS": {"name": "Pressure", "unit": "bar"},
    "TRQ": {"name": "Torque", "unit": "Nm"},
    "RPM": {"name": "Rotational Speed", "unit": "rpm"},
    "PWR": {"name": "Power Draw", "unit": "kW"},
    "FLW": {"name": "Flow Rate", "unit": "L/min"},
    "CUR": {"name": "Current", "unit": "A"},
    "HUM": {"name": "Humidity", "unit": "%"},
}

# Sensor ranges per machine type — [min_normal, max_normal, min_critical, max_critical]
SENSOR_RANGES: dict[str, dict[str, list[float]]] = {
    "HYP": {
        "TMP": [25.0, 65.0, 10.0, 85.0],
        "VIB": [0.5, 4.5, 0.0, 11.0],
        "PRS": [180.0, 250.0, 150.0, 280.0],
        "PWR": [45.0, 120.0, 0.0, 160.0],
    },
    "SRV": {
        "TMP": [20.0, 55.0, 10.0, 75.0],
        "VIB": [0.3, 3.5, 0.0, 8.0],
        "TRQ": [200.0, 800.0, 0.0, 1200.0],
        "RPM": [30.0, 120.0, 0.0, 150.0],
        "PWR": [25.0, 80.0, 0.0, 110.0],
    },
    "RBT": {
        "TMP": [20.0, 50.0, 10.0, 70.0],
        "CUR": [5.0, 35.0, 0.0, 50.0],
        "TRQ": [10.0, 150.0, 0.0, 200.0],
        "VIB": [0.1, 2.0, 0.0, 5.0],
        "PWR": [3.0, 25.0, 0.0, 40.0],
    },
    "OVN": {
        "TMP": [160.0, 200.0, 100.0, 240.0],
        "HUM": [5.0, 15.0, 0.0, 25.0],
        "PWR": [80.0, 200.0, 0.0, 260.0],
    },
    "PMP": {
        "PRS": [2.0, 6.0, 0.0, 8.0],
        "FLW": [15.0, 40.0, 0.0, 55.0],
        "TMP": [20.0, 45.0, 10.0, 60.0],
        "VIB": [0.2, 2.5, 0.0, 6.0],
        "PWR": [5.0, 20.0, 0.0, 30.0],
    },
    "TST": {
        "TMP": [18.0, 28.0, 10.0, 40.0],
        "PWR": [10.0, 60.0, 0.0, 80.0],
        "VIB": [0.1, 1.5, 0.0, 3.0],
    },
    "CNC": {
        "TMP": [25.0, 60.0, 10.0, 80.0],
        "VIB": [0.5, 5.0, 0.0, 12.0],
        "RPM": [1000.0, 12000.0, 0.0, 15000.0],
        "PWR": [15.0, 55.0, 0.0, 75.0],
    },
    "CNV": {
        "TMP": [20.0, 45.0, 10.0, 60.0],
        "VIB": [0.2, 2.0, 0.0, 5.0],
        "PWR": [2.0, 10.0, 0.0, 15.0],
        "RPM": [20.0, 60.0, 0.0, 80.0],
    },
}

# ─── Failure Modes (AI4I-inspired) ─────────────────────────────────────────────

FAILURE_MODES = {
    "TWF": "Tool Wear Failure",
    "HDF": "Heat Dissipation Failure",
    "PWF": "Power Failure",
    "OSF": "Overstrain Failure",
    "RNF": "Random Failure",
}

FAILURE_SEVERITIES = ["critical", "major", "minor"]
FAILURE_DETECTED_BY = ["operator", "sensor_alert", "inspection", "predictive_agent"]

# ─── Station-Specific Defect Types ─────────────────────────────────────────────

STATION_DEFECTS: dict[str, list[str]] = {
    "STP-01-PRS": ["crack", "wrinkle", "thinning", "springback", "burr"],
    "STP-02-PRS": ["split", "surface scratch", "galling", "misalignment"],
    "STP-03-TRM": ["slug pull", "oversized hole", "incomplete trim", "edge burr"],
    "WLD-01-UBD": ["weld spatter", "incomplete fusion", "porosity", "burn-through", "misalignment"],
    "WLD-02-SDP": ["crack", "undercut", "cold lap", "distortion"],
    "WLD-03-RCL": ["blow hole", "lack of penetration", "electrode wear mark"],
    "PNT-01-ECT": ["thin coverage", "bare spot", "crater", "drip"],
    "PNT-02-PRM": ["orange peel", "color mismatch", "fisheye", "solvent pop"],
    "PNT-03-CLR": ["runs/sags", "dust inclusion", "haze", "pinholes"],
    "ASM-01-PWR": ["torque out-of-spec", "bolt missing", "connector unseated", "fluid leak"],
    "ASM-02-INT": ["clip broken", "panel gap", "squeak/rattle", "wiring misroute"],
    "ASM-03-FNL": ["door alignment", "hood gap", "trunk seal", "trim fit"],
    "QAT-01-ALN": ["wheel alignment out-of-spec", "camber deviation", "toe deviation"],
    "QAT-02-WLT": ["seal failure", "drain plug missing", "glass bond gap"],
    "QAT-03-DYN": ["vibration at speed", "brake noise", "steering pull", "warning light"],
}

# ─── Shifts ────────────────────────────────────────────────────────────────────

@dataclass
class ShiftConfig:
    name: str
    start_hour: int
    end_hour: int
    crews: list[str] = field(default_factory=list)

SHIFTS = {
    "day": ShiftConfig(name="Day", start_hour=6, end_hour=14, crews=["Crew A", "Crew C"]),
    "swing": ShiftConfig(name="Swing", start_hour=14, end_hour=22, crews=["Crew B", "Crew D"]),
    "night": ShiftConfig(name="Night", start_hour=22, end_hour=6, crews=["Crew E", "Crew F"]),
}

DAILY_PRODUCTION_TARGET = 80

# ─── Quality ───────────────────────────────────────────────────────────────────

AQL_LEVELS = {
    "normal": {"aql": 1.0, "sample_ratio": 0.1},
    "tightened": {"aql": 0.65, "sample_ratio": 0.15},
    "reduced": {"aql": 2.5, "sample_ratio": 0.05},
}

QUALITY_DISPOSITIONS = ["accept", "reject", "rework", "scrap", "use-as-is", "return-to-supplier"]

# ─── Reliability Thresholds ────────────────────────────────────────────────────

MTBF_THRESHOLDS = {"good": 500.0, "warning": 200.0}  # hours
MTTR_THRESHOLDS = {"good": 2.0, "warning": 4.0}  # hours
AVAILABILITY_TARGET = 95.0  # percent
OEE_TARGET = 75.0  # percent
CPK_THRESHOLDS = {"good": 1.33, "warning": 1.0}

# ─── VIN Format ────────────────────────────────────────────────────────────────

VIN_PREFIX = "PEF"  # PrimeEV Factory


def generate_vin(model_code: str, year: int, sequence: int) -> str:
    """Generate a structured VIN: PEF-SD100-26-004521"""
    year_short = str(year)[-2:]
    return f"{VIN_PREFIX}-{model_code}-{year_short}-{sequence:06d}"


def generate_part_number(category: str, model_code: str, sequence: int) -> str:
    """Generate a structured part number: CHS-SD100-001"""
    return f"{category}-{model_code}-{sequence:03d}"


def generate_failure_id(station_id: str, year: int, month: int, sequence: int) -> str:
    """Generate a failure ID: FLR-STP01-2606-003"""
    station_short = station_id.replace("-", "")[:5]
    return f"FLR-{station_short}-{year % 100:02d}{month:02d}-{sequence:03d}"


def generate_work_order_id(year: int, month: int, sequence: int) -> str:
    """Generate a work order ID: WO-2606-00142"""
    return f"WO-{year % 100:02d}{month:02d}-{sequence:05d}"


def generate_inspection_id(inspection_type: str, sequence: int) -> str:
    """Generate an inspection ID: INS-DIM-026841"""
    return f"INS-{inspection_type}-{sequence:06d}"
