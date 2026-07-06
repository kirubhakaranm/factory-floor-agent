"""Postgres query builders for agent tools."""

from datetime import datetime

from sqlalchemy import func, select, text
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
    result = await session.execute(select(Machine).where(Machine.machine_id == machine_id))
    return result.scalar_one_or_none()


async def get_station_machines(session: AsyncSession, station_id: str) -> list[Machine]:
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
    stmt = select(EquipmentFailure)
    if machine_id:
        stmt = stmt.where(EquipmentFailure.machine_id == machine_id)
    if station_id:
        stmt = stmt.join(Machine).where(Machine.station_id == station_id)
    if failure_mode:
        stmt = stmt.where(EquipmentFailure.failure_mode == failure_mode)
    cutoff = datetime.now().replace(year=2026) - __import__("datetime").timedelta(days=days_back)
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
    stmt = select(SparePartInventory)
    if low_stock_only:
        stmt = stmt.where(SparePartInventory.quantity_on_hand <= SparePartInventory.reorder_point)
    result = await session.execute(stmt.limit(100))
    parts = list(result.scalars().all())
    if machine_id:
        parts = [p for p in parts if machine_id in (p.compatible_machines or [])]
    return parts
