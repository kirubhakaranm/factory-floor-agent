"""Maintenance and work order tools."""


def get_maintenance_history(
    machine_id: str,
    months_back: int = 3,
) -> str:
    """Get maintenance history for a machine including preventive and corrective actions.

    Args:
        machine_id: Machine identifier
        months_back: Months of history to retrieve

    Returns:
        List of maintenance events with type, trigger, duration, parts replaced, cost
    """
    return (
        f"Querying maintenance history for {machine_id} over last {months_back} months. "
        "Returns maint_id, type (preventive/corrective/predictive/overhaul), trigger, "
        "started_at, completed_at, duration_min, technician_id, parts_replaced, "
        "labor_hours, total_cost, machine_condition_before, machine_condition_after."
    )


def get_work_orders(
    machine_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
) -> str:
    """Get work orders filtered by machine, status, or priority.

    Args:
        machine_id: Filter by machine (optional)
        status: Filter by status: open, in_progress, completed (optional)
        priority: Filter by priority: critical, high, medium, low (optional)

    Returns:
        List of work orders with details
    """
    filters = []
    if machine_id:
        filters.append(f"machine={machine_id}")
    if status:
        filters.append(f"status={status}")
    if priority:
        filters.append(f"priority={priority}")
    return f"Querying work orders (filters: {', '.join(filters) or 'none'}). Returns wo_id, machine_id, type, priority, description, assigned_to, status, created_at, completed_at."


def create_work_order(
    machine_id: str,
    wo_type: str,
    priority: str,
    description: str,
) -> str:
    """Create a new work order for a machine.

    Args:
        machine_id: Machine requiring work
        wo_type: Type of work: preventive, corrective, predictive
        priority: Priority level: critical, high, medium, low
        description: Description of work needed

    Returns:
        Created work order ID and confirmation
    """
    return (
        f"Work order created: machine={machine_id}, type={wo_type}, "
        f"priority={priority}, description='{description}'. "
        "Assigned to next available technician on current shift."
    )
