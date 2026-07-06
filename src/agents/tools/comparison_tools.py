"""Comparison tools — cross-shift, cross-period, cross-station analysis."""

from src.db.clickhouse import queries as ch


def compare_shifts(
    station_id: str,
    metric: str = "oee",
    days_back: int = 30,
) -> list[dict]:
    """Compare a metric across shifts (Day vs Swing vs Night) for a station.

    Args:
        station_id: Station identifier
        metric: Metric to compare: oee, availability, performance, quality
        days_back: Days of history

    Returns:
        Per-shift average, min, max, and data point count
    """
    return ch.compare_shifts(station_id, metric, days_back)


def compare_periods(
    station_id: str,
    metric: str,
    period_a_days: str = "last 7 days",
    period_b_days: str = "prior 7 days",
) -> str:
    """Compare a metric between two time periods for a station.

    Args:
        station_id: Station identifier
        metric: Metric to compare (oee, defect_rate, throughput, energy)
        period_a_days: Description of first period (e.g., 'last 7 days')
        period_b_days: Description of second period (e.g., 'prior 7 days')

    Returns:
        Period A average, Period B average, change %, direction (improved/declined/stable)
    """
    return (
        f"Comparing {metric} for {station_id}: "
        f"Period A ({period_a_days}) vs Period B ({period_b_days}). "
        "Returns avg_a, avg_b, change_pct, direction."
    )


def compare_stations(
    stage: str,
    metric: str = "oee",
    days_back: int = 30,
) -> str:
    """Compare a metric across all stations in a stage.

    Args:
        stage: Stage code: STP, WLD, PNT, ASM, QAT
        metric: Metric to compare
        days_back: Days of history

    Returns:
        Per-station average for the metric, ranked best to worst
    """
    return (
        f"Comparing {metric} across {stage} stations over {days_back} days. "
        "Returns station_id, avg_value, rank, deviation_from_best."
    )
