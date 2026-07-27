"""Data loader — bulk inserts generated JSON data into Postgres and ClickHouse."""

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.postgres.models import (
    AqlScheme,
    Base,
    BillOfMaterials,
    Component,
    ComponentConsumption,
    ConsumablesInventory,
    Crew,
    DefectCode,
    DeviationRecord,
    DimensionalInspection,
    EquipmentFailure,
    FinishedGoods,
    InspectionPlan,
    InventoryTransaction,
    Line,
    Machine,
    MaintenanceHistory,
    MeasurementSpec,
    Operator,
    ProductionBatch,
    ProductionOrder,
    RawMaterial,
    RawMaterialInventory,
    ReceivingInspection,
    ReworkRecord,
    SamplingInspection,
    ScrapRecord,
    Shift,
    SparePartInventory,
    Station,
    Supplier,
    SupplierNcr,
    SupplierScorecard,
    Technician,
    VehicleModel,
    VinRegistry,
    VisualChecklist,
    WorkOrder,
)
from src.datagen.factory_model import (
    ALL_STATION_IDS,
    FACTORY_MACHINES,
    FACTORY_STATIONS,
    FACTORY_VEHICLE_MODELS,
    STAGE_ORDER,
)


def _parse_date(val: str | date | None) -> date | None:
    """Coerce a string or date value to a date, returning None if the input is None."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return datetime.fromisoformat(val).date()


def _parse_datetime(val: str | datetime | None) -> datetime | None:
    """Coerce a string or datetime value to a datetime, returning None if the input is None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(val)


def _load_json(path: Path) -> list[dict]:
    """Load a JSON array from a file, returning an empty list if the file does not exist."""
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_postgres(data_dir: Path) -> None:
    """Create tables and bulk insert all Postgres data."""
    engine = create_engine(settings.postgres_url_sync, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Factory structure (from constants, not generated)
        _load_factory_structure(session)

        # Product models + BOMs
        _load_product_data(session)

        # Measurement spec master table (normalizes tolerances out of dimensional_inspections)
        _load_measurement_specs(session)

        # Quality master data: defect catalog, inspection plans, AQL table
        _load_defect_codes(session)
        _load_inspection_plans(session)
        _load_aql_schemes(session)

        # Generated data
        _load_table(session, data_dir, "operators", Operator, {
            "hire_date": _parse_date,
        })
        _load_table(session, data_dir, "technicians", Technician)
        _load_table(session, data_dir, "crews", Crew)
        _load_table(session, data_dir, "shifts", Shift, {
            "date": _parse_date,
            "start_time": _parse_datetime,
            "end_time": _parse_datetime,
        })
        _load_table(session, data_dir, "suppliers", Supplier)
        _load_table(session, data_dir, "raw_materials", RawMaterial)
        _load_table(session, data_dir, "receiving_inspections", ReceivingInspection, {
            "inspection_date": _parse_date,
        })
        _load_table(session, data_dir, "supplier_scorecards", SupplierScorecard, {
            "month": _parse_date,
        }, exclude_fields={"id"})
        _load_table(session, data_dir, "supplier_ncrs", SupplierNcr, {
            "date": _parse_date,
        })
        _load_table(session, data_dir, "production_orders", ProductionOrder, {
            "due_date": _parse_date,
        })
        _load_table(session, data_dir, "production_batches", ProductionBatch, {
            "start_time": _parse_datetime,
            "end_time": _parse_datetime,
        })
        _load_table(session, data_dir, "vin_registry", VinRegistry, {
            "production_date": _parse_date,
        })
        _load_table(session, data_dir, "equipment_failures", EquipmentFailure, {
            "failure_start": _parse_datetime,
            "failure_end": _parse_datetime,
        })
        _load_table(session, data_dir, "maintenance_history", MaintenanceHistory, {
            "started_at": _parse_datetime,
            "completed_at": _parse_datetime,
        }, exclude_fields={"maint_id"})
        _load_table(session, data_dir, "work_orders", WorkOrder, {
            "created_at": _parse_datetime,
            "completed_at": _parse_datetime,
        })
        _load_table(session, data_dir, "dimensional_inspections", DimensionalInspection, {
            "timestamp": _parse_datetime,
        })
        _load_table(session, data_dir, "sampling_inspections", SamplingInspection, {
            "timestamp": _parse_datetime,
        })
        _load_table(session, data_dir, "visual_checklists", VisualChecklist, {
            "timestamp": _parse_datetime,
        })
        _load_table(session, data_dir, "rework_records", ReworkRecord, {
            "timestamp": _parse_datetime,
        })
        _load_table(session, data_dir, "scrap_records", ScrapRecord, {
            "timestamp": _parse_datetime,
        })
        _load_table(session, data_dir, "raw_material_inventory", RawMaterialInventory, {
            "last_counted": _parse_date,
        })
        _load_table(session, data_dir, "consumables_inventory", ConsumablesInventory)
        _load_table(session, data_dir, "spare_parts_inventory", SparePartInventory, {
            "last_used_date": _parse_date,
        }, exclude_fields={"id"})

        # Inline-generated tables: no JSON files, derived from existing data
        _load_component_consumption(session, data_dir)
        _load_inventory_transactions(session, data_dir)

        # Finished goods from VIN registry
        vins = _load_json(data_dir / "vin_registry.json")
        for v in vins:
            session.add(FinishedGoods(
                vin_id=v["vin_id"],
                completion_date=_parse_date(v["production_date"]),
                storage_location=f"LOT-{v.get('batch_id', 'A')[-3:]}",
            ))

        session.commit()
        print(f"  Postgres: all tables loaded")


def _load_factory_structure(session: Session) -> None:
    """Insert Line, Station, and Machine rows derived from factory constants."""
    for i, (stage_code, stage_name) in enumerate(zip(STAGE_ORDER, [
        "Stamping", "Welding", "Paint", "Assembly", "Quality & Test"
    ])):
        session.add(Line(line_id=f"{stage_code}-L1", stage=stage_code, name=f"{stage_name} Line 1"))

    for station_id, station in FACTORY_STATIONS.items():
        stage_code = station.stage
        session.add(Station(
            station_id=station_id,
            stage=stage_code,
            name=station.name,
            position=station.position,
            line_id=f"{stage_code}-L1",
        ))

    for machine_id, machine in FACTORY_MACHINES.items():
        session.add(Machine(
            machine_id=machine_id,
            station_id=machine.station_id,
            machine_type=machine.machine_type,
            model=machine.model,
            serial_number=f"SN-{machine_id[-5:].replace('-', '')}",
            criticality=machine.criticality,
            maintenance_interval_hrs=machine.maintenance_interval_hrs,
            total_operating_hours=14000.0,
            lifecycle_status="active",
        ))
    session.flush()


def _load_product_data(session: Session) -> None:
    """Insert VehicleModel, Component, and BillOfMaterials rows from the factory model."""
    seen_parts = set()
    for model_id, model in FACTORY_VEHICLE_MODELS.items():
        session.add(VehicleModel(
            model_id=model_id, name=model.name, year=model.year, variant=model.variant,
        ))
        session.flush()

        for comp in model.components:
            if comp.part_number not in seen_parts:
                seen_parts.add(comp.part_number)
                session.add(Component(
                    part_number=comp.part_number,
                    description=comp.description,
                    category=comp.category,
                    station_id=comp.station_id,
                    supplier_id=comp.supplier_id,
                    unit_cost=comp.unit_cost,
                ))
            session.add(BillOfMaterials(
                model_id=model_id,
                part_number=comp.part_number,
                quantity=1,
                station_id=comp.station_id,
            ))
    session.flush()


def _load_table(
    session: Session,
    data_dir: Path,
    filename: str,
    model_class: type,
    converters: dict | None = None,
    exclude_fields: set | None = None,
) -> None:
    """Bulk-insert rows from a JSON file into a SQLAlchemy model table in batches of 1000."""
    rows = _load_json(data_dir / f"{filename}.json")
    if not rows:
        return

    converters = converters or {}
    exclude_fields = exclude_fields or set()

    valid_columns = {c.key for c in model_class.__table__.columns}
    batch_size = 1000
    count = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        objects = []
        for row in batch:
            kwargs = {}
            for key, val in row.items():
                if key in exclude_fields or key not in valid_columns:
                    continue
                if key in converters:
                    val = converters[key](val)
                kwargs[key] = val
            objects.append(model_class(**kwargs))
        session.bulk_save_objects(objects)
        count += len(objects)

    session.flush()
    print(f"    {filename}: {count:,} rows")


def _load_measurement_specs(session: Session) -> None:
    """Generate 15 stations × 20 measurement names = 300 spec rows.
    Uses a fixed seed so nominal/tolerance values are reproducible and match what
    the quality generator produces (which also uses seed=42 per-station ordering).
    """
    rng = random.Random(42)
    effective_date = date(2026, 1, 1)
    count = 0
    for station_id in ALL_STATION_IDS:
        for i in range(1, 21):
            nominal = round(rng.uniform(5.0, 50.0), 3)
            tolerance = round(nominal * 0.02, 3)
            session.add(MeasurementSpec(
                station_id=station_id,
                measurement_name=f"dim_{i}",
                nominal=nominal,
                upper_tol=round(nominal + tolerance, 3),
                lower_tol=round(nominal - tolerance, 3),
                usl=round(nominal + tolerance * 1.5, 3),
                lsl=round(nominal - tolerance * 1.5, 3),
                effective_date=effective_date,
                drawing_ref=f"PE-DWG-{station_id[:3]}-{i:03d}",
            ))
            count += 1
    session.flush()
    print(f"    measurement_specs: {count:,} rows")


def _load_defect_codes(session: Session) -> None:
    """Expand STATION_DEFECTS into a queryable defect catalog with category/severity/detection."""
    from src.config.constants import STATION_DEFECTS

    # (category, severity, detection_method) per defect name
    _meta: dict[str, tuple[str, str, str]] = {
        # Stamping
        "crack":               ("structural",  "critical", "dimensional"),
        "wrinkle":             ("cosmetic",    "minor",    "visual"),
        "thinning":            ("structural",  "critical", "dimensional"),
        "springback":          ("dimensional", "major",    "dimensional"),
        "burr":                ("cosmetic",    "minor",    "visual"),
        "split":               ("structural",  "critical", "dimensional"),
        "surface scratch":     ("cosmetic",    "minor",    "visual"),
        "galling":             ("structural",  "major",    "visual"),
        "misalignment":        ("dimensional", "major",    "dimensional"),
        "slug pull":           ("functional",  "major",    "visual"),
        "oversized hole":      ("dimensional", "critical", "dimensional"),
        "incomplete trim":     ("dimensional", "major",    "dimensional"),
        "edge burr":           ("cosmetic",    "minor",    "visual"),
        # Welding
        "weld spatter":        ("cosmetic",    "minor",    "visual"),
        "incomplete fusion":   ("structural",  "critical", "spc"),
        "porosity":            ("structural",  "major",    "spc"),
        "burn-through":        ("structural",  "critical", "spc"),
        "undercut":            ("structural",  "major",    "spc"),
        "cold lap":            ("structural",  "major",    "spc"),
        "distortion":          ("dimensional", "major",    "dimensional"),
        "blow hole":           ("structural",  "critical", "spc"),
        "lack of penetration": ("structural",  "critical", "spc"),
        "electrode wear mark": ("cosmetic",    "minor",    "visual"),
        # Paint
        "thin coverage":       ("cosmetic",    "major",    "functional"),
        "bare spot":           ("cosmetic",    "critical", "visual"),
        "crater":              ("cosmetic",    "major",    "visual"),
        "drip":                ("cosmetic",    "minor",    "visual"),
        "orange peel":         ("cosmetic",    "minor",    "visual"),
        "color mismatch":      ("cosmetic",    "major",    "visual"),
        "fisheye":             ("cosmetic",    "major",    "visual"),
        "solvent pop":         ("cosmetic",    "minor",    "visual"),
        "runs/sags":           ("cosmetic",    "minor",    "visual"),
        "dust inclusion":      ("cosmetic",    "minor",    "visual"),
        "haze":                ("cosmetic",    "minor",    "visual"),
        "pinholes":            ("cosmetic",    "major",    "visual"),
        # Assembly
        "torque out-of-spec":  ("functional",  "critical", "functional"),
        "bolt missing":        ("safety",      "critical", "functional"),
        "connector unseated":  ("functional",  "critical", "functional"),
        "fluid leak":          ("safety",      "critical", "functional"),
        "clip broken":         ("functional",  "minor",    "visual"),
        "panel gap":           ("cosmetic",    "major",    "dimensional"),
        "squeak/rattle":       ("functional",  "minor",    "functional"),
        "wiring misroute":     ("functional",  "major",    "visual"),
        "door alignment":      ("functional",  "major",    "dimensional"),
        "hood gap":            ("cosmetic",    "major",    "dimensional"),
        "trunk seal":          ("functional",  "major",    "functional"),
        "trim fit":            ("cosmetic",    "minor",    "visual"),
        # QAT
        "wheel alignment out-of-spec": ("functional", "critical", "functional"),
        "camber deviation":    ("functional",  "major",    "functional"),
        "toe deviation":       ("functional",  "major",    "functional"),
        "seal failure":        ("functional",  "critical", "functional"),
        "drain plug missing":  ("safety",      "critical", "functional"),
        "glass bond gap":      ("structural",  "major",    "functional"),
        "vibration at speed":  ("functional",  "major",    "functional"),
        "brake noise":         ("safety",      "major",    "functional"),
        "steering pull":       ("functional",  "major",    "functional"),
        "warning light":       ("functional",  "critical", "functional"),
    }

    count = 0
    seen: set[str] = set()
    for station_id, defects in STATION_DEFECTS.items():
        stage = station_id[:3]
        for i, defect_name in enumerate(defects, start=1):
            # Stable code: stage prefix + 3-letter abbrev + 3-digit seq
            abbrev = defect_name.replace(" ", "_").replace("/", "_")[:6].upper()
            code = f"{stage}-{abbrev}-{i:03d}"
            if code in seen:
                code = f"{stage}-{abbrev}-{count:03d}"
            seen.add(code)

            cat, sev, detect = _meta.get(defect_name, ("functional", "major", "visual"))
            session.add(DefectCode(
                defect_code=code,
                name=defect_name,
                stage=stage,
                station_id=station_id,
                category=cat,
                severity=sev,
                detection_method=detect,
                description=f"{sev.capitalize()} {cat} defect at {station_id}. Detected via {detect} inspection.",
            ))
            count += 1

    session.flush()
    print(f"    defect_codes: {count:,} rows")


def _load_inspection_plans(session: Session) -> None:
    """Generate one or more inspection plan rows per station covering all check types."""
    from src.datagen.factory_model import ALL_STATION_IDS

    # (characteristic_name, inspection_type, measurement_method, frequency,
    #  sample_size_pct, control_chart_enabled, responsible_role)
    _stage_plans: dict[str, list[tuple]] = {
        "STP": [
            ("panel_thickness",    "dimensional", "CMM",           "every_unit",  None,  True,  "quality_tech"),
            ("draw_depth",         "dimensional", "CMM",           "first_off",   None,  False, "quality_tech"),
            ("surface_roughness",  "spc",         "profilometer",  "hourly",      None,  True,  "quality_tech"),
            ("blank_position",     "spc",         "optical_gauge", "every_unit",  None,  True,  "operator"),
            ("visual_surface",     "visual",      "visual_100pct", "every_unit",  None,  False, "operator"),
            ("aql_incoming",       "sampling",    "aql_sampling",  "aql_sample",  10.0,  False, "quality_tech"),
        ],
        "WLD": [
            ("nugget_diameter",    "spc",         "destructive_pull_test", "aql_sample", 5.0, True, "quality_tech"),
            ("weld_current",       "spc",         "spc_chart",     "every_unit",  None,  True,  "operator"),
            ("electrode_force",    "spc",         "spc_chart",     "every_unit",  None,  True,  "operator"),
            ("visual_weld",        "visual",      "visual_100pct", "every_unit",  None,  False, "operator"),
            ("weld_joint_xray",    "functional",  "xray_sample",   "aql_sample",  5.0,  False, "quality_tech"),
            ("aql_weld_quality",   "sampling",    "aql_sampling",  "aql_sample",  10.0,  False, "quality_tech"),
        ],
        "PNT": [
            ("film_thickness",     "functional",  "dry_film_gauge", "every_unit", None,  True,  "quality_tech"),
            ("gloss_level",        "spc",         "glossmeter",    "hourly",      None,  True,  "quality_tech"),
            ("color_delta_e",      "spc",         "spectrophotometer", "per_batch", None, True, "quality_tech"),
            ("visual_paint",       "visual",      "visual_100pct", "every_unit",  None,  False, "operator"),
            ("adhesion_test",      "functional",  "cross_cut_test","aql_sample",  5.0,  False, "quality_tech"),
        ],
        "ASM": [
            ("torque_value",       "spc",         "torque_analyzer","every_unit", None,  True,  "operator"),
            ("bolt_angle",         "spc",         "angle_gauge",   "every_unit",  None,  True,  "operator"),
            ("gap_measurement",    "dimensional", "gap_gauge",     "every_unit",  None,  False, "operator"),
            ("visual_assembly",    "visual",      "visual_100pct", "every_unit",  None,  False, "operator"),
            ("connector_force",    "functional",  "push_pull_gauge","aql_sample", 5.0,  False, "quality_tech"),
        ],
        "QAT": [
            ("wheel_alignment",    "functional",  "alignment_rack","every_unit",  None,  True,  "quality_tech"),
            ("water_leak_test",    "functional",  "water_spray",   "every_unit",  None,  False, "quality_tech"),
            ("dyno_vibration",     "functional",  "dyno_test",     "every_unit",  None,  True,  "quality_tech"),
            ("brake_performance",  "functional",  "brake_analyser","every_unit",  None,  True,  "quality_tech"),
            ("visual_final",       "visual",      "visual_100pct", "every_unit",  None,  False, "operator"),
            ("final_aql",          "sampling",    "aql_sampling",  "aql_sample",  10.0,  False, "quality_tech"),
        ],
    }

    count = 0
    for station_id in ALL_STATION_IDS:
        stage = station_id[:3]
        plans = _stage_plans.get(stage, [])
        for char_name, insp_type, method, freq, smp_pct, ctrl_chart, role in plans:
            session.add(InspectionPlan(
                station_id=station_id,
                characteristic_name=char_name,
                inspection_type=insp_type,
                measurement_method=method,
                frequency=freq,
                sample_size_pct=smp_pct,
                control_chart_enabled=ctrl_chart,
                responsible_role=role,
            ))
            count += 1

    session.flush()
    print(f"    inspection_plans: {count:,} rows")


def _load_aql_schemes(session: Session) -> None:
    """Fixed ISO 2859-1–inspired AQL table (simplified to 3 inspection levels × 9 lot bands)."""
    # (lot_min, lot_max, sample_code, normal_sz, normal_ac, tightened_sz, tightened_ac, reduced_sz, reduced_ac)
    _bands = [
        (2,    8,    "B",  2,   0,  3,   0,  2,  0),
        (9,    15,   "C",  3,   0,  5,   0,  2,  0),
        (16,   25,   "D",  5,   0,  8,   0,  3,  0),
        (26,   50,   "E",  8,   0,  13,  0,  5,  0),
        (51,   90,   "F",  13,  1,  20,  0,  8,  0),
        (91,   150,  "G",  20,  1,  32,  1,  13, 1),
        (151,  280,  "H",  32,  2,  50,  1,  20, 1),
        (281,  500,  "J",  50,  3,  80,  2,  32, 2),
        (501,  1200, "K",  80,  5,  125, 3,  50, 3),
    ]

    levels = [
        ("normal",    1.0),
        ("tightened", 0.65),
        ("reduced",   2.5),
    ]

    count = 0
    for lot_min, lot_max, code, n_sz, n_ac, t_sz, t_ac, r_sz, r_ac in _bands:
        for level, aql_pct in levels:
            if level == "normal":
                sz, ac = n_sz, n_ac
            elif level == "tightened":
                sz, ac = t_sz, t_ac
            else:
                sz, ac = r_sz, r_ac
            session.add(AqlScheme(
                inspection_level=level,
                aql_percent=aql_pct,
                lot_size_min=lot_min,
                lot_size_max=lot_max,
                sample_size=sz,
                accept_number=ac,
                reject_number=ac + 1,
                sample_code=code,
            ))
            count += 1

    session.flush()
    print(f"    aql_schemes: {count:,} rows")


def _load_component_consumption(session: Session, data_dir: Path) -> None:
    """Derive one component-consumption row per BOM component per production batch.
    Enables supplier lot → batch → VIN traceability queries.
    lot_number is NULL here; it gets linked via sampling_inspections post-hoc.
    """
    batches = _load_json(data_dir / "production_batches.json")
    if not batches:
        return
    count = 0
    for batch in batches:
        batch_id = batch["batch_id"]
        model_id = batch.get("model_id")
        units = batch.get("units_produced", 0)
        # start_time is a datetime string; extract date for consumed_date
        start_raw = batch.get("start_time") or batch.get("consumed_date")
        consumed_date_val = _parse_datetime(start_raw).date() if start_raw else None
        if consumed_date_val is None:
            continue

        model = FACTORY_VEHICLE_MODELS.get(model_id)
        if model is None:
            continue

        for comp in model.components:
            session.add(ComponentConsumption(
                batch_id=batch_id,
                consumed_date=consumed_date_val,
                station_id=comp.station_id,
                part_number=comp.part_number,
                model_id=model_id,
                lot_number=None,
                qty_consumed=max(1, units),
            ))
            count += 1

        if count % 10000 == 0:
            session.flush()

    session.flush()
    print(f"    component_consumption: {count:,} rows")


def _load_inventory_transactions(session: Session, data_dir: Path) -> None:
    """Generate inventory movement log from existing inventory snapshots.
    Raw materials: weekly receipts (positive qty).
    Consumables: 3 daily issues per station (negative qty, one per shift).
    Date range derived from the production_batches span.
    """
    batches = _load_json(data_dir / "production_batches.json")
    if batches:
        dates = [_parse_datetime(b["start_time"]).date() for b in batches if b.get("start_time")]
        range_start = min(dates) if dates else date(2026, 1, 1)
        range_end = max(dates) if dates else date(2026, 6, 30)
    else:
        range_start, range_end = date(2026, 1, 1), date(2026, 6, 30)

    rng = random.Random(999)
    count = 0

    # Weekly raw material receipts
    raw_materials = _load_json(data_dir / "raw_materials.json")
    total_days = (range_end - range_start).days
    for rm in raw_materials:
        material_id = rm.get("material_id")
        if not material_id:
            continue
        for week in range(total_days // 7 + 1):
            receipt_day = range_start + timedelta(weeks=week)
            if receipt_day > range_end:
                break
            receipt_dt = datetime(receipt_day.year, receipt_day.month, receipt_day.day,
                                  rng.randint(6, 16))
            session.add(InventoryTransaction(
                txn_datetime=receipt_dt,
                item_type="raw_material",
                item_id=material_id,
                station_id=None,
                qty_change=rng.randint(200, 800),
                reason="replenishment",
                ref_id=f"PO-{week:04d}-{material_id[-3:]}",
            ))
            count += 1

    # Daily consumable issues (3 per day — one per shift)
    consumables = _load_json(data_dir / "consumables_inventory.json")
    shift_hours = [6, 14, 22]
    for cons in consumables:
        item_id = cons.get("item_id")
        station_id = cons.get("station_id")
        usage_rate = float(cons.get("usage_rate_per_shift", 1) or 1)
        if not item_id:
            continue
        for day_offset in range(total_days):
            day = range_start + timedelta(days=day_offset)
            for shift_hour in shift_hours:
                txn_dt = datetime(day.year, day.month, day.day, shift_hour,
                                  rng.randint(0, 59))
                qty = -max(1, round(usage_rate * rng.uniform(0.8, 1.2)))
                session.add(InventoryTransaction(
                    txn_datetime=txn_dt,
                    item_type="consumable",
                    item_id=item_id,
                    station_id=station_id,
                    qty_change=qty,
                    reason="production",
                ))
                count += 1

        if count % 20000 == 0:
            session.flush()

    session.flush()
    print(f"    inventory_transactions: {count:,} rows")


def load_clickhouse(data_dir: Path) -> None:
    """Bulk insert all ClickHouse data."""
    from src.db.clickhouse.client import get_clickhouse_client

    client = get_clickhouse_client()

    ch_tables = {
        "sensor_readings": [
            "timestamp", "machine_id", "station_id", "sensor_type", "value", "unit",
        ],
        "energy_consumption": [
            "timestamp", "station_id", "power_kw", "cumulative_kwh", "load_type",
        ],
        "oee_metrics": [
            "timestamp", "station_id", "shift", "availability", "performance", "quality", "oee",
        ],
        "spc_measurements": [
            "timestamp", "station_id", "parameter", "value", "ucl", "lcl", "usl", "lsl",
            "target", "cp", "cpk",
        ],
        "degradation_state": [
            "timestamp", "machine_id", "health_index", "rul_hours", "component",
        ],
        "machine_reliability_metrics": [
            "machine_id", "period", "period_start", "mtbf_hrs", "mttr_hrs", "mttf_hrs",
            "availability_pct", "failure_rate", "total_downtime_hrs", "planned_downtime_hrs",
            "unplanned_downtime_hrs", "num_failures", "num_repairs", "total_repair_cost",
            "reliability_score",
        ],
        "process_capability_history": [
            "timestamp", "station_id", "parameter", "cp", "cpk", "pp", "ppk",
            "out_of_control_signals", "trending_alert",
        ],
    }

    for table_name, columns in ch_tables.items():
        file_path = data_dir / f"{table_name}.json"
        if not file_path.exists():
            continue

        data = _load_json(file_path)
        if not data:
            continue

        # Insert in batches
        batch_size = 50000
        total = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            rows = []
            for row in batch:
                parsed_row = []
                for col in columns:
                    val = row.get(col)
                    if col in ("timestamp", "period_start") and isinstance(val, str):
                        val = datetime.fromisoformat(val)
                    parsed_row.append(val)
                rows.append(parsed_row)
            client.insert(table_name, rows, column_names=columns)
            total += len(batch)

        print(f"    {table_name}: {total:,} rows")

    print(f"  ClickHouse: all tables loaded")
