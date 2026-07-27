"""Equipment failure tools — query failure history and active alerts."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.postgres import queries as pg


def get_failure_history(
    machine_id: str,
    months_back: Annotated[int, Field(ge=1, le=36, description="Months of history (1–36)")] = 3,
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum records (1–500)")] = 50,
) -> list[dict] | str:
    """[ACTION]: Retrieve all recorded equipment failures for a machine. [TARGET]: equipment_failures table (Postgres).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier from the factory topology
    (e.g. STP-01-PRS-HYP01). months_back is anchored to the latest failure date in the database,
    not wall-clock time.

    [OUTPUT GUARANTEE]: Returns a list of failure records ordered newest-first, each containing:
    failure_id, failure_mode, failure_type (TWF/HDF/PWF/OSF/RNF), component_failed, severity,
    detected_by, failure_start, failure_end, downtime_min, production_units_lost, root_cause,
    corrective_action, preventive_action, cost_parts, cost_labor, cost_lost_production, linked_wo_id.
    Empty list means no failures recorded in the window — not an error.

    [NEGATIVE BOUNDARY]: Cannot retrieve failures for machines not in the equipment_failures table.
    Cannot return failures outside the months_back window. Does not return active/open work orders —
    use get_work_orders for that. Do not expand months_back arbitrarily to find more failures.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')
        months_back: Months of history anchored to latest record (default 3)
        limit: Maximum records to return (default 50)

    Returns:
        List of failure dicts, newest first. Empty list if no failures in window.
    """
    return pg.sync_get_failure_history(machine_id, months_back, limit)


def get_active_alerts(
    station_id: str | None = None,
    severity: Literal["critical", "major", "minor"] | None = None,
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of history (1–365)")] = 7,
) -> list[dict] | str:
    """[ACTION]: Retrieve recent equipment failures as active alerts. [TARGET]: equipment_failures table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. STP-01-PRS) if provided.
    severity must be one of the Literal values if provided. Alerts are proxied from recent failures
    — there is no separate real-time alert stream queryable here.

    [OUTPUT GUARANTEE]: Returns failures from the last days_back days (anchored to latest record),
    filtered by station and/or severity. Each row contains: failure_id, machine_id, station_id,
    failure_mode, failure_type, severity, detected_by, failure_start, downtime_min, corrective_action.
    Empty list means no recent failures — equipment operating without recorded incidents.

    [NEGATIVE BOUNDARY]: Cannot return sub-minute streaming alerts from Kafka — those require the
    live alert feed. Cannot return predictive/threshold warnings, only confirmed failure events.
    Do not retry with wider date windows if empty; report clean status to the user.

    Args:
        station_id: Filter by station (optional, e.g. 'STP-01-PRS')
        severity: Filter by severity: 'critical', 'major', or 'minor' (optional)
        days_back: How many days back to look (default 7, anchored to latest DB record)

    Returns:
        List of recent failure dicts. Empty list if equipment operating cleanly.
    """
    return pg.sync_get_recent_failures(station_id, severity, days_back)


def get_failure_by_id(failure_id: str) -> dict | str:
    """[ACTION]: Retrieve the complete record for a single failure event by ID. [TARGET]: equipment_failures table (Postgres).

    [INPUT PREREQUISITE]: failure_id must be a known failure identifier in format
    FLR-{STATION}-{YYMM}-{SEQ} (e.g. 'FLR-STP01-2606-003'). Obtain IDs from get_failure_history
    before calling this tool.

    [OUTPUT GUARANTEE]: Returns a single dict with the full failure record: all fields from
    get_failure_history plus the complete root_cause, corrective_action, preventive_action narrative,
    and all cost breakdown fields.

    [NEGATIVE BOUNDARY]: Cannot retrieve failures by machine, date range, or any attribute other
    than failure_id. Cannot return work orders or maintenance records — use get_work_orders or
    get_maintenance_history for those.

    Args:
        failure_id: Failure identifier (e.g. 'FLR-STP01-2606-003')

    Returns:
        Complete failure record dict, or TERMINAL string if not found.
    """
    record = pg.sync_get_failure_by_id(failure_id)
    if not record:
        return (
            f"TERMINAL: Failure ID '{failure_id}' not found in the database. "
            "Verify the failure_id from get_failure_history output. "
            "Do not retry — ask the user to confirm the correct ID."
        )
    return record
