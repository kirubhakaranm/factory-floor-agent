"""Data loader — bulk inserts generated JSON data into Postgres and ClickHouse."""

import json
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.postgres.models import (
    Base,
    BillOfMaterials,
    Component,
    ConsumablesInventory,
    Crew,
    DeviationRecord,
    DimensionalInspection,
    EquipmentFailure,
    FinishedGoods,
    Line,
    Machine,
    MaintenanceHistory,
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
    FACTORY_MACHINES,
    FACTORY_STATIONS,
    FACTORY_VEHICLE_MODELS,
    STAGE_ORDER,
)


def _parse_date(val: str | date | None) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return datetime.fromisoformat(val).date()


def _parse_datetime(val: str | datetime | None) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(val)


def _load_json(path: Path) -> list[dict]:
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
            "timestamp": _parse_date,
        })
        _load_table(session, data_dir, "scrap_records", ScrapRecord, {
            "timestamp": _parse_date,
        })
        _load_table(session, data_dir, "raw_material_inventory", RawMaterialInventory, {
            "last_counted": _parse_date,
        })
        _load_table(session, data_dir, "consumables_inventory", ConsumablesInventory)
        _load_table(session, data_dir, "spare_parts_inventory", SparePartInventory, {
            "last_used_date": _parse_date,
        }, exclude_fields={"id"})

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
