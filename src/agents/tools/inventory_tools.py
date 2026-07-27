"""Inventory tools — spare parts, raw materials, consumables, WIP status,
and inventory transaction history."""

from typing import Literal

from src.db.postgres import queries as pg


def get_spare_parts(
    machine_id: str | None = None,
    low_stock_only: bool = False,
) -> list[dict]:
    """[ACTION]: Retrieve spare parts inventory, optionally filtered by compatible machine or low stock flag. [TARGET]: spare_parts_inventory table (Postgres).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier if provided.
    No minimum parameters required — returns all parts if called with no args.

    [OUTPUT GUARANTEE]: Returns spare parts rows with: part_number, description,
    compatible_machines, quantity_on_hand, reorder_point, lead_time_days, unit_cost,
    location_bin, low_stock (bool). Empty list is unexpected — the inventory table always
    has entries; an empty result may indicate an incorrect machine_id filter.

    [NEGATIVE BOUNDARY]: Cannot return consumables — use get_consumables_level for those.
    Cannot return raw materials — use get_raw_material_stock. Does not show usage history —
    use get_inventory_transaction_history for that.

    Args:
        machine_id: Filter by compatible machine (optional)
        low_stock_only: If True, return only parts at or below reorder point

    Returns:
        List of spare part dicts.
    """
    return pg.sync_get_spare_parts(machine_id, low_stock_only)


def get_raw_material_stock() -> list[dict]:
    """[ACTION]: Retrieve current raw material inventory levels with reorder status for all materials. [TARGET]: raw_material_inventory table (Postgres).

    [INPUT PREREQUISITE]: No parameters required. Returns the full raw material inventory snapshot.

    [OUTPUT GUARANTEE]: Returns all raw materials with: material_id, description, unit, quantity,
    reorder_point, reorder_qty, last_counted, status ('OK' / 'LOW' / 'CRITICAL').
    'LOW' means quantity ≤ reorder_point. 'CRITICAL' means quantity ≤ 0.
    Rows ordered CRITICAL → LOW → OK then by material_id.

    [NEGATIVE BOUNDARY]: Cannot return supplier lead times — use get_supplier_scorecard for that.
    Cannot return WIP or finished goods — use get_wip_status or query finished_goods separately.
    Snapshot represents last physical count; does not update in real-time.

    Returns:
        List of all raw material dicts with reorder status.
    """
    return pg.sync_get_raw_material_stock()


def get_consumables_level(station_id: str) -> list[dict]:
    """[ACTION]: Retrieve consumables inventory for a station with estimated shifts remaining. [TARGET]: consumables_inventory table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'WLD-01-UBD').

    [OUTPUT GUARANTEE]: Returns consumable items for the station with: item_id, description,
    quantity, min_level, usage_rate_per_shift, estimated_shifts_remaining. Items are sorted
    by estimated_shifts_remaining ascending (most urgent first).

    [NEGATIVE BOUNDARY]: Cannot return spare parts — use get_spare_parts. Cannot return
    raw materials — use get_raw_material_stock. Empty list means no consumables tracked
    for this station (not a data error).

    Args:
        station_id: Station identifier (e.g. 'WLD-01-UBD')

    Returns:
        List of consumable dicts sorted most-urgent first.
    """
    return pg.sync_get_consumables_level(station_id)


def get_wip_status() -> list[dict] | str:
    """[ACTION]: Retrieve work-in-progress count and utilization at each station. [TARGET]: wip_inventory table (Postgres).

    [INPUT PREREQUISITE]: No parameters required. Returns WIP snapshot for all 15 stations.

    [OUTPUT GUARANTEE]: Returns one row per station with: station_id, station_name, count
    (vehicles currently in process), max_capacity, utilization_pct. High utilization_pct
    (>80%) indicates potential bottleneck accumulation.

    [NEGATIVE BOUNDARY]: Cannot return individual VIN locations — use trace_vin_history for that.
    WIP count is a snapshot; it does not reflect real-time conveyor state.

    Returns:
        List of per-station WIP dicts. TERMINAL string if table unavailable.
    """
    try:
        data = pg.sync_get_wip_status()
    except Exception as e:
        return (
            f"TERMINAL: WIP inventory data unavailable ({type(e).__name__}). "
            "The wip_inventory table may not exist or be populated. "
            "Do not retry — report that WIP data is unavailable."
        )
    if not data:
        return (
            "TERMINAL: WIP inventory table returned no rows. "
            "The wip_inventory table may not be populated. "
            "Do not retry — report that WIP data is unavailable."
        )
    return data


def get_inventory_transaction_history(
    item_id: str | None = None,
    item_type: Literal["raw_material", "consumable", "spare_part"] | None = None,
    station_id: str | None = None,
    days_back: int = 30,
    limit: int = 100,
) -> list[dict]:
    """[ACTION]: Retrieve inventory receipt and consumption transactions over time. [TARGET]: inventory_transactions table (Postgres).

    [INPUT PREREQUISITE]: All filters are optional. item_type must be a Literal value if provided.
    Use this for RCA: 'how much hydraulic fluid was consumed at STP-01-PRS on June 15?' or
    'when was the last replenishment of RAW-STL-001?'

    [OUTPUT GUARANTEE]: Returns transaction rows with: txn_id, txn_datetime, item_type, item_id,
    station_id, qty_change (positive = receipt/replenishment, negative = consumption/issue),
    reason, ref_id, performed_by. Ordered newest-first.

    [NEGATIVE BOUNDARY]: Cannot return current stock levels — use get_raw_material_stock or
    get_spare_parts for that. Cannot return transactions older than days_back window.

    Args:
        item_id: Filter by specific item ID — material_id or consumable item_id (optional)
        item_type: Filter by type: 'raw_material', 'consumable', or 'spare_part' (optional)
        station_id: Filter by station (optional)
        days_back: How many days of history (default 30)
        limit: Maximum rows (default 100)

    Returns:
        List of transaction dicts.
    """
    return pg.sync_get_inventory_transactions(item_id, item_type, station_id, days_back, limit)
