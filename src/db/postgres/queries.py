"""Postgres query builders for agent tools.

Two sections:
  - Async ORM functions (used by FastAPI routes via get_session dependency)
  - Sync text-SQL functions (used directly by agent tools, same process)
"""

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres.models import (
    DimensionalInspection,
    EquipmentFailure,
    Machine,
    MaintenanceHistory,
    ProductionBatch,
    ReworkRecord,
    SamplingInspection,
    ScrapRecord,
    SparePartInventory,
    Station,
    Supplier,
    SupplierScorecard,
    VinRegistry,
    VisualChecklist,
    WorkOrder,
)


async def get_machine(session: AsyncSession, machine_id: str) -> Machine | None:
    """Return a Machine row by primary key, or None if not found."""
    result = await session.execute(select(Machine).where(Machine.machine_id == machine_id))
    return result.scalar_one_or_none()


async def get_station_machines(session: AsyncSession, station_id: str) -> list[Machine]:
    """Return all Machine rows assigned to a station."""
    result = await session.execute(
        select(Machine).where(Machine.station_id == station_id)
    )
    return list(result.scalars().all())


async def get_failure_history(
    session: AsyncSession,
    machine_id: str | None = None,
    station_id: str | None = None,
    days_back: int = 30,
    failure_mode: str | None = None,
    limit: int = 50,
) -> list[EquipmentFailure]:
    """Return recent EquipmentFailure rows filtered by machine, station, mode, and lookback window."""
    stmt = select(EquipmentFailure)
    if machine_id:
        stmt = stmt.where(EquipmentFailure.machine_id == machine_id)
    if station_id:
        stmt = stmt.join(Machine).where(Machine.station_id == station_id)
    if failure_mode:
        stmt = stmt.where(EquipmentFailure.failure_mode == failure_mode)
    cutoff = datetime.now().replace(year=2026) - timedelta(days=days_back)
    stmt = stmt.where(EquipmentFailure.failure_start >= cutoff)
    stmt = stmt.order_by(EquipmentFailure.failure_start.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_work_orders(
    session: AsyncSession,
    machine_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 50,
) -> list[WorkOrder]:
    """Return WorkOrder rows filtered by machine, status, and priority."""
    stmt = select(WorkOrder)
    if machine_id:
        stmt = stmt.where(WorkOrder.machine_id == machine_id)
    if status:
        stmt = stmt.where(WorkOrder.status == status)
    if priority:
        stmt = stmt.where(WorkOrder.priority == priority)
    stmt = stmt.order_by(WorkOrder.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_inspection_results(
    session: AsyncSession,
    station_id: str | None = None,
    result_filter: str | None = None,
    limit: int = 100,
) -> list[DimensionalInspection]:
    """Return DimensionalInspection rows for a station, optionally filtered by pass/fail result."""
    stmt = select(DimensionalInspection)
    if station_id:
        stmt = stmt.where(DimensionalInspection.station_id == station_id)
    if result_filter:
        stmt = stmt.where(DimensionalInspection.result == result_filter)
    stmt = stmt.order_by(DimensionalInspection.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_defect_rates(
    session: AsyncSession,
    station_id: str,
) -> dict[str, float]:
    """Get pass/fail rates for a station."""
    total = await session.execute(
        select(func.count()).where(DimensionalInspection.station_id == station_id)
    )
    fails = await session.execute(
        select(func.count()).where(
            DimensionalInspection.station_id == station_id,
            DimensionalInspection.result == "fail",
        )
    )
    t = total.scalar() or 1
    f = fails.scalar() or 0
    return {"total": t, "fails": f, "defect_rate": round(f / t * 100, 2)}


async def get_rework_history(
    session: AsyncSession,
    station_id: str | None = None,
    limit: int = 50,
) -> list[ReworkRecord]:
    """Return recent ReworkRecord rows for a station, newest first."""
    stmt = select(ReworkRecord)
    if station_id:
        stmt = stmt.where(ReworkRecord.station_id == station_id)
    stmt = stmt.order_by(ReworkRecord.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_vin_history(session: AsyncSession, vin_id: str) -> dict:
    """Get complete production history for a VIN."""
    vin = await session.execute(select(VinRegistry).where(VinRegistry.vin_id == vin_id))
    vin_record = vin.scalar_one_or_none()
    if not vin_record:
        return {"error": f"VIN {vin_id} not found"}

    inspections = await session.execute(
        select(DimensionalInspection).where(DimensionalInspection.vin_id == vin_id)
    )
    reworks = await session.execute(
        select(ReworkRecord).where(ReworkRecord.vin_id == vin_id)
    )
    scraps = await session.execute(
        select(ScrapRecord).where(ScrapRecord.vin_id == vin_id)
    )

    return {
        "vin": vin_record,
        "inspections": list(inspections.scalars().all()),
        "reworks": list(reworks.scalars().all()),
        "scraps": list(scraps.scalars().all()),
    }


async def get_supplier_scorecard(
    session: AsyncSession,
    supplier_id: str,
) -> list[SupplierScorecard]:
    """Return monthly SupplierScorecard rows for a supplier, newest first."""
    result = await session.execute(
        select(SupplierScorecard)
        .where(SupplierScorecard.supplier_id == supplier_id)
        .order_by(SupplierScorecard.month.desc())
    )
    return list(result.scalars().all())


async def get_spare_parts(
    session: AsyncSession,
    machine_id: str | None = None,
    low_stock_only: bool = False,
) -> list[SparePartInventory]:
    """Return spare part inventory rows, optionally filtered by machine compatibility or low stock."""
    stmt = select(SparePartInventory)
    if low_stock_only:
        stmt = stmt.where(SparePartInventory.quantity_on_hand <= SparePartInventory.reorder_point)
    result = await session.execute(stmt.limit(100))
    parts = list(result.scalars().all())
    if machine_id:
        parts = [p for p in parts if machine_id in (p.compatible_machines or [])]
    return parts


# ─── Sync helpers (used by agent tools) ────────────────────────────────────────

_sync_engine: Engine | None = None


def _get_sync_engine() -> Engine:
    """Return (or create) the module-level synchronous SQLAlchemy engine."""
    global _sync_engine
    if _sync_engine is None:
        from src.config.settings import settings
        _sync_engine = create_engine(settings.postgres_url_sync, pool_pre_ping=True, pool_size=5)
    return _sync_engine


def _q(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Execute a parameterised SQL query and return results as a list of dicts."""
    with _get_sync_engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        cols = list(result.keys())
        return [dict(zip(cols, row)) for row in result]


def _q1(sql: str, params: dict[str, Any] | None = None) -> dict | None:
    """Execute a parameterised SQL query and return the first row as a dict, or None."""
    rows = _q(sql, params)
    return rows[0] if rows else None


# Quality inspections

def sync_get_dimensional_results(station_id: str, result_filter: str | None = None, limit: int = 50) -> list[dict]:
    """Return dimensional inspection results for a station, optionally filtered by pass/fail."""
    return _q("""
        SELECT insp_id, station_id, measurement_name, nominal,
               upper_tol, lower_tol, actual_value, result, timestamp
        FROM dimensional_inspections
        WHERE station_id = :station_id
          AND (:result_filter IS NULL OR result = :result_filter)
        ORDER BY timestamp DESC LIMIT :limit
    """, {"station_id": station_id, "result_filter": result_filter, "limit": limit})


def sync_get_sampling_results(station_id: str, limit: int = 20) -> list[dict]:
    """Return AQL sampling inspection results for a station."""
    return _q("""
        SELECT insp_id, station_id, lot_number, lot_size, sample_size,
               aql_level, accept_number, reject_number, defects_found,
               disposition, inspection_type, timestamp
        FROM sampling_inspections
        WHERE station_id = :station_id
        ORDER BY timestamp DESC LIMIT :limit
    """, {"station_id": station_id, "limit": limit})


def sync_get_visual_checklist(station_id: str, limit: int = 20) -> list[dict]:
    """Return visual checklist records for a station, newest first."""
    return _q("""
        SELECT checklist_id, vin_id, station_id, checkpoint_items, defect_category, timestamp
        FROM visual_checklists
        WHERE station_id = :station_id
        ORDER BY timestamp DESC LIMIT :limit
    """, {"station_id": station_id, "limit": limit})


def sync_get_defect_rates(station_id: str) -> dict:
    """Return pass/fail counts and defect rate percentage for a station."""
    return _q1("""
        SELECT COUNT(*) AS total_inspections,
               SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END) AS fail_count,
               ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS defect_rate_pct,
               ROUND(100.0*SUM(CASE WHEN result='pass' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS first_pass_yield_pct
        FROM dimensional_inspections WHERE station_id = :station_id
    """, {"station_id": station_id}) or {}


def sync_get_rework_history(station_id: str, limit: int = 30) -> list[dict]:
    """Return rework records for a station, newest first."""
    return _q("""
        SELECT rework_id, vin_id, station_id, defect_type,
               rework_action, rework_time_min, re_inspect_result, cost, timestamp
        FROM rework_records
        WHERE station_id = :station_id
        ORDER BY timestamp DESC LIMIT :limit
    """, {"station_id": station_id, "limit": limit})


# Quality master data

def sync_get_defect_catalog(
    station_id: str | None = None, stage: str | None = None,
    severity: str | None = None, category: str | None = None,
) -> list[dict]:
    """Return defect catalog entries filtered by station, stage, severity, or category."""
    return _q("""
        SELECT defect_code, name, stage, station_id,
               category, severity, detection_method, description
        FROM defect_codes
        WHERE (:station_id IS NULL OR station_id = :station_id)
          AND (:stage      IS NULL OR stage      = :stage)
          AND (:severity   IS NULL OR severity   = :severity)
          AND (:category   IS NULL OR category   = :category)
        ORDER BY station_id, severity DESC, name
    """, {"station_id": station_id, "stage": stage, "severity": severity, "category": category})


def sync_get_inspection_plan(station_id: str) -> list[dict]:
    """Return all inspection plan rows for a station."""
    return _q("""
        SELECT plan_id, station_id, characteristic_name, inspection_type,
               measurement_method, frequency, sample_size_pct,
               control_chart_enabled, responsible_role
        FROM inspection_plans
        WHERE station_id = :station_id
        ORDER BY inspection_type, characteristic_name
    """, {"station_id": station_id})


def sync_get_aql_recommendation(lot_size: int, inspection_level: str = "normal") -> dict:
    """Return the AQL scheme row matching a lot size and inspection level."""
    return _q1("""
        SELECT scheme_id, inspection_level, aql_percent, lot_size_min, lot_size_max,
               sample_size, accept_number, reject_number, sample_code
        FROM aql_schemes
        WHERE inspection_level = :level
          AND :lot_size BETWEEN lot_size_min AND lot_size_max
        LIMIT 1
    """, {"level": inspection_level, "lot_size": lot_size}) or {}


def sync_get_measurement_specs(station_id: str, measurement_name: str | None = None) -> list[dict]:
    """Return active measurement specification rows for a station, optionally by name."""
    return _q("""
        SELECT spec_id, station_id, measurement_name, nominal,
               upper_tol, lower_tol, usl, lsl, effective_date, drawing_ref
        FROM measurement_specs
        WHERE station_id = :station_id
          AND (:measurement_name IS NULL OR measurement_name = :measurement_name)
          AND superseded_date IS NULL
        ORDER BY measurement_name
    """, {"station_id": station_id, "measurement_name": measurement_name})


# Supply chain

def sync_get_receiving_inspections(
    supplier_id: str | None = None, result_filter: str | None = None, limit: int = 20,
) -> list[dict]:
    """Return receiving inspection records filtered by supplier and result."""
    return _q("""
        SELECT ri_id, material_id, supplier_id, lot_number,
               inspection_date, result, disposition, first_article_status
        FROM receiving_inspections
        WHERE (:supplier_id   IS NULL OR supplier_id = :supplier_id)
          AND (:result_filter IS NULL OR result      = :result_filter)
        ORDER BY inspection_date DESC LIMIT :limit
    """, {"supplier_id": supplier_id, "result_filter": result_filter, "limit": limit})


def sync_get_supplier_scorecard(supplier_id: str) -> list[dict]:
    """Return the last 12 months of scorecard data for a supplier joined with supplier name."""
    return _q("""
        SELECT s.name AS supplier_name, sc.supplier_id, sc.month,
               sc.defect_ppm, sc.on_time_pct, sc.quality_score, sc.lot_count,
               CASE WHEN sc.quality_score>=90 THEN 'A'
                    WHEN sc.quality_score>=75 THEN 'B'
                    WHEN sc.quality_score>=60 THEN 'C'
                    ELSE 'D' END AS grade
        FROM supplier_scorecards sc
        JOIN suppliers s ON sc.supplier_id = s.supplier_id
        WHERE sc.supplier_id = :supplier_id
        ORDER BY sc.month DESC LIMIT 12
    """, {"supplier_id": supplier_id})


def sync_get_supplier_ncrs(supplier_id: str | None = None, limit: int = 20) -> list[dict]:
    """Return supplier NCR records, optionally filtered by supplier ID."""
    return _q("""
        SELECT ncr_id, supplier_id, lot_id, issue, disposition, date
        FROM supplier_ncrs
        WHERE (:supplier_id IS NULL OR supplier_id = :supplier_id)
        ORDER BY date DESC LIMIT :limit
    """, {"supplier_id": supplier_id, "limit": limit})


def sync_get_component_consumption(
    batch_id: str | None = None, lot_number: str | None = None,
    part_number: str | None = None, limit: int = 50,
) -> list[dict]:
    """Return component consumption rows for traceability queries by batch, lot, or part."""
    return _q("""
        SELECT id, batch_id, consumed_date, station_id,
               part_number, model_id, lot_number, qty_consumed
        FROM component_consumption
        WHERE (:batch_id    IS NULL OR batch_id    = :batch_id)
          AND (:lot_number  IS NULL OR lot_number  = :lot_number)
          AND (:part_number IS NULL OR part_number = :part_number)
        ORDER BY consumed_date DESC LIMIT :limit
    """, {"batch_id": batch_id, "lot_number": lot_number, "part_number": part_number, "limit": limit})


# Inventory

def sync_get_raw_material_stock() -> list[dict]:
    """Return current raw material stock with OK / LOW / CRITICAL status labels."""
    return _q("""
        SELECT material_id, description, unit, quantity, reorder_point, reorder_qty, last_counted,
               CASE WHEN quantity <= 0              THEN 'CRITICAL'
                    WHEN quantity <= reorder_point  THEN 'LOW'
                    ELSE 'OK' END AS status
        FROM raw_material_inventory
        ORDER BY status DESC, material_id
    """)


def sync_get_consumables_level(station_id: str) -> list[dict]:
    """Return consumable stock levels for a station with estimated shifts remaining."""
    return _q("""
        SELECT item_id, station_id, description, quantity, min_level,
               usage_rate_per_shift,
               CASE WHEN usage_rate_per_shift > 0
                    THEN ROUND((quantity/usage_rate_per_shift)::numeric, 1)
                    ELSE NULL END AS estimated_shifts_remaining
        FROM consumables_inventory
        WHERE station_id = :station_id
        ORDER BY estimated_shifts_remaining ASC NULLS LAST
    """, {"station_id": station_id})


def sync_get_spare_parts(machine_id: str | None = None, low_stock_only: bool = False) -> list[dict]:
    """Return spare parts inventory, optionally filtered by machine or low-stock flag."""
    # Fetch all rows, then filter in Python.
    # compatible_machines is JSON (not PG ARRAY) so ANY() won't work.
    # Boolean parameter negation in text() is also unreliable across drivers.
    rows = _q("""
        SELECT part_number, description, compatible_machines,
               quantity_on_hand, reorder_point,
               lead_time_days, unit_cost, location_bin,
               (quantity_on_hand <= reorder_point) AS low_stock
        FROM spare_parts_inventory
        ORDER BY part_number
    """)
    if machine_id:
        rows = [r for r in rows if machine_id in (r.get("compatible_machines") or [])]
    if low_stock_only:
        rows = [r for r in rows if r.get("low_stock")]
    return rows


def sync_get_inventory_transactions(
    item_id: str | None = None, item_type: str | None = None,
    station_id: str | None = None, days_back: int = 30, limit: int = 100,
) -> list[dict]:
    """Return inventory transaction log entries filtered by item, type, station, and date window."""
    since = datetime.now() - timedelta(days=days_back)
    return _q("""
        SELECT txn_id, txn_datetime, item_type, item_id, station_id,
               qty_change, reason, ref_id, performed_by
        FROM inventory_transactions
        WHERE txn_datetime >= :since
          AND (:item_id    IS NULL OR item_id    = :item_id)
          AND (:item_type  IS NULL OR item_type  = :item_type)
          AND (:station_id IS NULL OR station_id = :station_id)
        ORDER BY txn_datetime DESC LIMIT :limit
    """, {"since": since, "item_id": item_id, "item_type": item_type,
          "station_id": station_id, "limit": limit})


# VIN traceability


def sync_get_vin_history(vin_id: str) -> dict:
    """Full production trail for a VIN: registry, batch, finished goods, station quality context."""
    vin = _q1("""
        SELECT vr.vin_id, vr.model_id, vm.name AS model_name,
               vr.production_date::text AS production_date,
               vr.batch_id, vr.status
        FROM vin_registry vr
        JOIN vehicle_models vm ON vr.model_id = vm.model_id
        WHERE vr.vin_id = :vin_id
    """, {"vin_id": vin_id})
    if not vin:
        return {"error": f"VIN {vin_id} not found in registry"}

    batch = _q1("""
        SELECT pb.batch_id, pb.line_id,
               pb.start_time::text AS start_time, pb.end_time::text AS end_time,
               pb.units_produced, pb.units_passed,
               ROUND(100.0 * pb.units_passed / NULLIF(pb.units_produced, 0), 1) AS batch_yield_pct
        FROM production_batches pb
        WHERE pb.batch_id = :batch_id
    """, {"batch_id": vin["batch_id"]}) or {}

    fg = _q1("""
        SELECT completion_date::text AS completion_date,
               storage_location, ship_date::text AS ship_date
        FROM finished_goods WHERE vin_id = :vin_id
    """, {"vin_id": vin_id}) or {}

    # Station-level sampling inspections from the VIN's production date (batch quality context)
    prod_date = vin["production_date"]
    station_quality = _q("""
        SELECT station_id, inspection_type,
               lot_size, sample_size, defects_found, disposition
        FROM sampling_inspections
        WHERE timestamp::date = :prod_date
        ORDER BY station_id, inspection_type
    """, {"prod_date": prod_date})

    return {
        "vin": vin,
        "batch": batch,
        "finished_goods": fg,
        "station_quality_context": station_quality,
        "note": (
            "Individual unit inspection results are tracked at batch level. "
            "station_quality_context shows all station sampling results on the production date."
        ),
    }


def sync_get_vin_quality_summary(vin_id: str) -> dict:
    """Quality scorecard for a VIN: batch yield, station sampling pass/fail, final disposition."""
    vin = _q1("""
        SELECT vr.vin_id, vr.model_id, vm.name AS model_name,
               vr.production_date::text AS production_date,
               vr.batch_id, vr.status
        FROM vin_registry vr
        JOIN vehicle_models vm ON vr.model_id = vm.model_id
        WHERE vr.vin_id = :vin_id
    """, {"vin_id": vin_id})
    if not vin:
        return {"error": f"VIN {vin_id} not found"}

    batch = _q1("""
        SELECT pb.units_produced, pb.units_passed,
               ROUND(100.0 * pb.units_passed / NULLIF(pb.units_produced, 0), 1) AS batch_yield_pct
        FROM production_batches pb WHERE pb.batch_id = :batch_id
    """, {"batch_id": vin["batch_id"]}) or {}

    # Per-stage sampling summary on production date
    prod_date = vin["production_date"]
    stage_summary = _q("""
        SELECT SUBSTRING(station_id, 1, 3) AS stage,
               COUNT(*) AS inspection_lots,
               SUM(defects_found) AS total_defects,
               SUM(CASE WHEN disposition = 'accept' THEN 1 ELSE 0 END) AS lots_accepted,
               SUM(CASE WHEN disposition != 'accept' THEN 1 ELSE 0 END) AS lots_rejected
        FROM sampling_inspections
        WHERE timestamp::date = :prod_date
        GROUP BY SUBSTRING(station_id, 1, 3)
        ORDER BY stage
    """, {"prod_date": prod_date})

    fg = _q1("""
        SELECT completion_date::text, storage_location, ship_date::text
        FROM finished_goods WHERE vin_id = :vin_id
    """, {"vin_id": vin_id}) or {}

    return {
        "vin_id": vin_id,
        "model": vin["model_name"],
        "production_date": vin["production_date"],
        "status": vin["status"],
        "batch_id": vin["batch_id"],
        "batch_yield": batch,
        "stage_quality_on_production_date": stage_summary,
        "final_disposition": fg,
    }


# Maintenance history


# Equipment failures

def sync_get_failure_history(machine_id: str, months_back: int = 3, limit: int = 50) -> list[dict]:
    """Equipment failures for a machine anchored to latest record date."""
    anchor = _q1("SELECT max(failure_start) AS anchor FROM equipment_failures")
    if not anchor or anchor["anchor"] is None:
        return []
    cutoff = anchor["anchor"] - timedelta(days=months_back * 30)
    return _q("""
        SELECT failure_id, machine_id, failure_mode, failure_type,
               component_failed, severity, detected_by,
               failure_start::text AS failure_start,
               failure_end::text AS failure_end,
               downtime_min, production_units_lost,
               root_cause, corrective_action, preventive_action,
               cost_parts, cost_labor, cost_lost_production, linked_wo_id
        FROM equipment_failures
        WHERE machine_id = :machine_id
          AND failure_start >= :cutoff
        ORDER BY failure_start DESC
        LIMIT :limit
    """, {"machine_id": machine_id, "cutoff": cutoff, "limit": limit})


def sync_get_failure_by_id(failure_id: str) -> dict | None:
    """Return a single equipment failure record by its ID, or None if not found."""
    return _q1("""
        SELECT failure_id, machine_id, failure_mode, failure_type,
               component_failed, severity, detected_by,
               failure_start::text AS failure_start,
               failure_end::text AS failure_end,
               downtime_min, production_units_lost,
               root_cause, corrective_action, preventive_action,
               cost_parts, cost_labor, cost_lost_production, linked_wo_id
        FROM equipment_failures
        WHERE failure_id = :failure_id
    """, {"failure_id": failure_id})


def sync_get_recent_failures(
    station_id: str | None = None,
    severity: str | None = None,
    days_back: int = 7,
    limit: int = 20,
) -> list[dict]:
    """Recent failures across a station — used as active-alert proxy."""
    anchor = _q1("SELECT max(failure_start) AS anchor FROM equipment_failures")
    if not anchor or anchor["anchor"] is None:
        return []
    cutoff = anchor["anchor"] - timedelta(days=days_back)
    return _q("""
        SELECT ef.failure_id, ef.machine_id, m.station_id,
               ef.failure_mode, ef.failure_type, ef.severity, ef.detected_by,
               ef.failure_start::text AS failure_start,
               ef.downtime_min, ef.corrective_action
        FROM equipment_failures ef
        JOIN machines m ON ef.machine_id = m.machine_id
        WHERE ef.failure_start >= :cutoff
          AND (:station_id IS NULL OR m.station_id = :station_id)
          AND (:severity   IS NULL OR ef.severity  = :severity)
        ORDER BY ef.failure_start DESC
        LIMIT :limit
    """, {"cutoff": cutoff, "station_id": station_id, "severity": severity, "limit": limit})


# Work orders

def sync_get_work_orders(
    machine_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Return work orders filtered by machine, status, and priority."""
    return _q("""
        SELECT wo_id, machine_id, type, priority, description,
               assigned_to, status,
               created_at::text AS created_at,
               completed_at::text AS completed_at
        FROM work_orders
        WHERE (:machine_id IS NULL OR machine_id = :machine_id)
          AND (:status     IS NULL OR status     = :status)
          AND (:priority   IS NULL OR priority   = :priority)
        ORDER BY created_at DESC LIMIT :limit
    """, {"machine_id": machine_id, "status": status, "priority": priority, "limit": limit})


def sync_create_work_order(
    machine_id: str, wo_type: str, priority: str, description: str,
) -> dict:
    """Insert a new open work order and return its ID and metadata."""
    now = datetime.now()
    prefix = f"WO-{now.strftime('%y%m')}"
    count_row = _q1(f"SELECT COUNT(*) AS cnt FROM work_orders WHERE wo_id LIKE '{prefix}%'")
    seq = (count_row["cnt"] if count_row else 0) + 1
    wo_id = f"{prefix}-{seq:05d}"
    with _get_sync_engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO work_orders (wo_id, machine_id, type, priority, description, status, created_at)
            VALUES (:wo_id, :machine_id, :type, :priority, :description, 'open', NOW())
        """), {"wo_id": wo_id, "machine_id": machine_id, "type": wo_type,
               "priority": priority, "description": description})
    return {
        "wo_id": wo_id, "status": "open", "machine_id": machine_id,
        "type": wo_type, "priority": priority, "created_at": now.isoformat(),
    }


# WIP status

def sync_get_wip_status() -> list[dict]:
    """Return WIP inventory count and utilisation percentage for every station."""
    return _q("""
        SELECT w.station_id, s.name AS station_name,
               w.count, w.max_capacity,
               ROUND(100.0 * w.count / NULLIF(w.max_capacity, 0), 1) AS utilization_pct
        FROM wip_inventory w
        JOIN stations s ON w.station_id = s.station_id
        ORDER BY s.position
    """)


# Production throughput

def sync_get_batch_status(batch_id: str) -> dict | None:
    """Return status and yield data for a single production batch, or None if not found."""
    return _q1("""
        SELECT batch_id, line_id, model_id,
               start_time::text AS start_time,
               end_time::text AS end_time,
               units_produced, units_passed,
               ROUND(100.0 * units_passed / NULLIF(units_produced, 0), 1) AS yield_pct
        FROM production_batches
        WHERE batch_id = :batch_id
    """, {"batch_id": batch_id})


def sync_get_throughput(days_back: int = 7) -> list[dict]:
    """Return daily production throughput and yield by model for the last N days."""
    anchor = _q1("SELECT max(start_time)::date AS anchor FROM production_batches")
    if not anchor or anchor["anchor"] is None:
        return []
    cutoff = anchor["anchor"] - timedelta(days=days_back)
    return _q("""
        SELECT start_time::date AS date,
               model_id,
               SUM(units_produced) AS units_produced,
               SUM(units_passed)   AS units_passed,
               ROUND(100.0 * SUM(units_passed) / NULLIF(SUM(units_produced), 0), 1) AS yield_pct
        FROM production_batches
        WHERE start_time::date >= :cutoff
        GROUP BY start_time::date, model_id
        ORDER BY date DESC, model_id
    """, {"cutoff": cutoff})


def sync_get_maintenance_history(machine_id: str, months_back: int = 3) -> list[dict]:
    """Maintenance events for a machine over the last N months (anchored to latest record date)."""
    anchor = _q1("SELECT max(started_at) AS anchor FROM maintenance_history")
    if not anchor or anchor["anchor"] is None:
        return []
    cutoff = anchor["anchor"] - timedelta(days=months_back * 30)
    return _q("""
        SELECT maint_id, machine_id, type, trigger,
               started_at::text AS started_at, completed_at::text AS completed_at,
               duration_min, technician_id, parts_replaced,
               labor_hours, total_cost,
               machine_condition_before, machine_condition_after, wo_id
        FROM maintenance_history
        WHERE machine_id = :machine_id
          AND started_at >= :cutoff
        ORDER BY started_at DESC
    """, {"machine_id": machine_id, "cutoff": cutoff})


# ─── Conversation persistence ───────────────────────────────────────────────


def sync_write_message(session_id: str, role: str, content: str, created_at: datetime) -> None:
    """Persist a single conversation message (user or assistant turn) to the database."""
    with _get_sync_engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO conversation_messages (session_id, role, content, created_at)
            VALUES (:sid, :role, :content, :ts)
        """), {"sid": session_id, "role": role, "content": content, "ts": created_at})


def sync_list_sessions(limit: int = 50) -> list[dict]:
    """Return a list of recent chat sessions with their start time and message count."""
    return _q("""
        SELECT session_id,
               MIN(created_at) AS created_at,
               COUNT(*) AS message_count
        FROM conversation_messages
        GROUP BY session_id
        ORDER BY MIN(created_at) DESC
        LIMIT :limit
    """, {"limit": limit})


def sync_get_session_messages(session_id: str) -> list[dict]:
    """Return all messages in a chat session ordered chronologically."""
    return _q("""
        SELECT role, content, created_at::text AS timestamp
        FROM conversation_messages
        WHERE session_id = :sid
        ORDER BY created_at
    """, {"sid": session_id})


