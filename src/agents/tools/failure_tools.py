"""Equipment failure tools — query failure history and active alerts."""

from src.db.clickhouse import queries as ch


def get_failure_history(
    machine_id: str,
    days_back: int = 30,
) -> str:
    """Get recent equipment failure history for a machine.

    Args:
        machine_id: Machine identifier (e.g., 'STP-01-PRS-HYP01')
        days_back: Number of days of history to retrieve

    Returns:
        Formatted failure history text
    """
    # In production, this queries Postgres. For tool definition, return description.
    return (
        f"Querying failure history for {machine_id} over last {days_back} days. "
        "Returns failure_id, failure_mode, failure_type, component_failed, severity, "
        "detected_by, downtime_min, root_cause, corrective_action, cost_parts, cost_labor."
    )


def get_active_alerts(
    station_id: str | None = None,
    severity: str | None = None,
) -> str:
    """Get currently active equipment alerts.

    Args:
        station_id: Filter by station (optional)
        severity: Filter by severity: critical, major, minor (optional)

    Returns:
        List of active alerts with machine, type, and severity
    """
    filters = []
    if station_id:
        filters.append(f"station={station_id}")
    if severity:
        filters.append(f"severity={severity}")
    filter_str = ", ".join(filters) if filters else "none"
    return f"Querying active alerts (filters: {filter_str}). Returns alert_id, machine_id, alert_type, severity, sensor_value, threshold, timestamp."


def get_failure_by_id(failure_id: str) -> str:
    """Get detailed information about a specific failure event.

    Args:
        failure_id: Failure identifier (e.g., 'FLR-STP01-2606-003')

    Returns:
        Complete failure record with timeline, root cause, actions, and costs
    """
    return (
        f"Querying failure {failure_id}. Returns complete record: machine_id, failure_mode, "
        "failure_type, component_failed, severity, detected_by, failure_start, failure_end, "
        "downtime_min, production_units_lost, root_cause, corrective_action, preventive_action, "
        "cost_parts, cost_labor, cost_lost_production, linked_wo_id."
    )
