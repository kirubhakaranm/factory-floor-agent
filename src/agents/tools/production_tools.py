"""Production tools — batches, OEE, cycle times, throughput."""

from src.db.clickhouse import queries as ch


def get_batch_status(batch_id: str) -> str:
    """Get production batch details — units produced, passed, yield.

    Args:
        batch_id: Batch identifier (e.g., 'B-000042')

    Returns:
        Batch record with model_id, start/end time, units_produced, units_passed, yield
    """
    return f"Querying batch {batch_id}. Returns batch_id, model_id, line_id, start_time, end_time, units_produced, units_passed, yield_pct."


def get_oee_metrics(
    station_id: str,
    shift: str | None = None,
    days_back: int = 30,
) -> list[dict]:
    """Get OEE (Overall Equipment Effectiveness) metrics for a station.

    OEE = Availability × Performance × Quality. Target: ≥75%.

    Args:
        station_id: Station identifier
        shift: Filter by shift name: Day, Swing, Night (optional)
        days_back: Days of history

    Returns:
        Daily OEE breakdown: availability, performance, quality, oee
    """
    return ch.get_oee_metrics(station_id, shift, days_back)


def get_cycle_times(station_id: str, days_back: int = 7) -> str:
    """Get cycle time statistics for a station.

    Args:
        station_id: Station identifier
        days_back: Days of history

    Returns:
        Cycle time mean, min, max, std dev, and comparison to target
    """
    from src.datagen.factory_model import FACTORY_STATIONS
    station = FACTORY_STATIONS.get(station_id)
    target = station.cycle_time_sec if station else 60.0
    return (
        f"Querying cycle times for {station_id} over {days_back} days. "
        f"Target cycle time: {target}s. Returns mean, min, max, std_dev, "
        f"pct_above_target, total_cycles."
    )


def get_throughput(
    line_id: str | None = None,
    days_back: int = 7,
) -> str:
    """Get daily production throughput (units completed per day).

    Args:
        line_id: Filter by line (optional). If None, returns factory total.
        days_back: Days of history

    Returns:
        Daily units produced, units passed, yield, by model
    """
    return (
        f"Querying throughput (line: {line_id or 'all'}, days: {days_back}). "
        "Returns date, model_id, units_produced, units_passed, yield_pct."
    )
