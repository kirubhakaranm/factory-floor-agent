"""Inventory tools — spare parts, raw materials, consumables, WIP status."""


def get_spare_parts(
    machine_id: str | None = None,
    low_stock_only: bool = False,
) -> str:
    """Get spare parts inventory, optionally filtered by compatible machine or low stock.

    Args:
        machine_id: Filter by compatible machine (optional)
        low_stock_only: If True, only return parts at or below reorder point

    Returns:
        Spare parts with quantity_on_hand, reorder_point, lead_time_days, unit_cost, location_bin
    """
    filters = []
    if machine_id:
        filters.append(f"compatible with {machine_id}")
    if low_stock_only:
        filters.append("low stock only")
    return (
        f"Querying spare parts ({', '.join(filters) or 'all'}). "
        "Returns part_number, description, quantity_on_hand, reorder_point, "
        "lead_time_days, unit_cost, location_bin."
    )


def get_raw_material_stock() -> str:
    """Get current raw material inventory levels with reorder status.

    Returns:
        Material inventory with quantity, reorder_point, status (OK/LOW/CRITICAL)
    """
    return (
        "Querying raw material inventory. Returns material_id, description, "
        "unit, quantity, reorder_point, reorder_qty, status."
    )


def get_consumables_level(station_id: str) -> str:
    """Get consumables inventory for a station (weld tips, filters, lubricant, etc.).

    Args:
        station_id: Station identifier

    Returns:
        Consumable items with quantity, min_level, usage_rate_per_shift, estimated shifts until empty
    """
    return (
        f"Querying consumables for {station_id}. Returns item_id, description, "
        "quantity, min_level, usage_rate_per_shift, estimated_shifts_remaining."
    )


def get_wip_status() -> str:
    """Get work-in-progress inventory at each station — how many vehicles are in the pipeline.

    Returns:
        Per-station WIP count, max capacity, utilization percentage
    """
    return (
        "Querying WIP inventory. Returns station_id, count, max_capacity, "
        "utilization_pct for each station."
    )
