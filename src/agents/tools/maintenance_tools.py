"""Maintenance and work order tools."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.postgres import queries as pg


def get_maintenance_history(
    machine_id: str,
    months_back: Annotated[int, Field(ge=1, le=36, description="Months of history (1–36)")] = 3,
) -> list[dict] | str:
    """[ACTION]: Retrieve maintenance events for a machine (preventive, corrective, predictive, overhaul). [TARGET]: maintenance_history table (Postgres).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier (e.g. 'STP-01-PRS-HYP01').
    months_back window is anchored to the latest record in the table, not wall-clock time.

    [OUTPUT GUARANTEE]: Returns maintenance events newest-first, each containing: maint_id,
    machine_id, type, trigger, started_at, completed_at, duration_min, technician_id,
    parts_replaced, labor_hours, total_cost, machine_condition_before, machine_condition_after,
    wo_id. Empty list means no maintenance performed in the window.

    [NEGATIVE BOUNDARY]: Cannot return scheduled future maintenance — only completed events.
    Cannot return work orders — use get_work_orders for that. Does not aggregate MTBF/MTTR —
    use get_mtbf_mttr for reliability metrics.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')
        months_back: Months of history anchored to latest record (default 3)

    Returns:
        List of maintenance event dicts. Empty list if no events in window.
    """
    return pg.sync_get_maintenance_history(machine_id, months_back)


def get_work_orders(
    machine_id: str | None = None,
    status: Literal["open", "in_progress", "completed"] | None = None,
    priority: Literal["critical", "high", "medium", "low"] | None = None,
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum records (1–500)")] = 50,
) -> list[dict] | str:
    """[ACTION]: Retrieve work orders filtered by machine, status, and/or priority. [TARGET]: work_orders table (Postgres).

    [INPUT PREREQUISITE]: All filters are optional. status and priority must be Literal values
    if provided. Without any filter, returns the most recent 50 work orders factory-wide.

    [OUTPUT GUARANTEE]: Returns work order records ordered newest-first, each containing: wo_id,
    machine_id, type, priority, description, assigned_to, status, created_at, completed_at.
    completed_at is null for open/in_progress orders. Empty list means no matching work orders.

    [NEGATIVE BOUNDARY]: Cannot create new work orders — use create_work_order for that.
    Cannot filter by date range or station — filter by machine_id and status only.

    Args:
        machine_id: Filter by machine (optional)
        status: Filter by status: 'open', 'in_progress', or 'completed' (optional)
        priority: Filter by priority: 'critical', 'high', 'medium', or 'low' (optional)
        limit: Maximum records to return (default 50)

    Returns:
        List of work order dicts. Empty list if no matching work orders.
    """
    return pg.sync_get_work_orders(machine_id, status, priority, limit)


def create_work_order(
    machine_id: str,
    wo_type: Literal["preventive", "corrective", "predictive"],
    priority: Literal["critical", "high", "medium", "low"],
    description: str,
) -> dict | str:
    """[ACTION]: Create a new open work order and persist it to the database. [TARGET]: work_orders table (Postgres) — write operation.

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier. wo_type and priority
    must be Literal values. description must be a clear, specific task description.
    Do not call this tool speculatively — confirm the machine and task with the user first.

    [OUTPUT GUARANTEE]: Returns a confirmation dict with: wo_id (format WO-YYMM-XXXXX),
    status='open', machine_id, type, priority, created_at. The work order is immediately
    visible in get_work_orders.

    [NEGATIVE BOUNDARY]: Cannot assign to a specific technician — assignments are manual.
    Cannot create work orders for non-existent machines. Does not generate a PDF —
    use schedule_maintenance in action_tools for a formal maintenance notice with PDF.

    Args:
        machine_id: Machine requiring work (e.g. 'STP-01-PRS-HYP01')
        wo_type: Type of work: 'preventive', 'corrective', or 'predictive'
        priority: Priority level: 'critical', 'high', 'medium', or 'low'
        description: Clear description of the work to be performed

    Returns:
        Confirmation dict with wo_id and status, or TERMINAL string on failure.
    """
    try:
        return pg.sync_create_work_order(machine_id, wo_type, priority, description)
    except Exception as exc:
        return (
            f"TERMINAL: Work order creation failed — {exc}. "
            "Do not retry automatically. Report the error to the user and ask how to proceed."
        )
