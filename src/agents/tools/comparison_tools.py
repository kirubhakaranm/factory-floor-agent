"""Comparison tools — cross-shift, cross-period, cross-station analysis."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.clickhouse import queries as ch


def compare_shifts(
    station_id: str,
    metric: Literal["oee", "availability", "performance", "quality"] = "oee",
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of history (1–365)")] = 30,
) -> list[dict] | str:
    """[ACTION]: Compare a production metric across Day, Swing, and Night shifts for a station. [TARGET]: oee_metrics table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'ASM-01-PWR').
    metric must be one of the Literal values. days_back is anchored to the latest record.

    [OUTPUT GUARANTEE]: Returns one row per shift (Day/Swing/Night) with: shift, avg_value,
    min_value, max_value, data_points. Values are decimals (0.0–1.0) for OEE components.
    Rows are ordered alphabetically by shift name.

    [NEGATIVE BOUNDARY]: Cannot compare across stations — this is single-station only.
    Cannot return per-day shift data — use get_oee_metrics for that. Does not include
    statistical significance testing.

    Args:
        station_id: Station identifier (e.g. 'ASM-01-PWR')
        metric: Metric to compare: 'oee', 'availability', 'performance', or 'quality'
        days_back: Days of history (default 30)

    Returns:
        List of per-shift dicts. Empty list if no OEE data for the station.
    """
    data = ch.compare_shifts(station_id, metric, days_back)
    if not data:
        return (
            f"TERMINAL: No OEE shift data for station '{station_id}' "
            f"(metric={metric}, days_back={days_back}). "
            "Verify the station_id. Do not retry."
        )
    return data


def compare_periods(
    station_id: str,
    metric: Literal["oee", "availability", "performance", "quality"] = "oee",
    recent_days: Annotated[int, Field(ge=1, le=365, description="Length of the recent period in days (1–365)")] = 7,
    prior_days: Annotated[int, Field(ge=1, le=365, description="Length of the prior period in days (1–365)")] = 7,
) -> list[dict] | str:
    """[ACTION]: Compare a metric between the most recent N days and the preceding N days for a station. [TARGET]: oee_metrics table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code. metric must be one of the
    Literal values. recent_days defines Period A (most recent); prior_days defines Period B
    (the period immediately before Period A).

    [OUTPUT GUARANTEE]: Returns two rows — one labeled 'period_a' (recent) and one 'period_b'
    (prior) — each with: period, avg_value, min_value, max_value, data_points.
    Compute change_pct as (period_a.avg - period_b.avg) / period_b.avg * 100.

    [NEGATIVE BOUNDARY]: Cannot compare non-contiguous periods. Cannot compare across stations
    — call per station. Cannot be used for shift-level comparison — use compare_shifts for that.

    Args:
        station_id: Station identifier (e.g. 'ASM-01-PWR')
        metric: Metric to compare: 'oee', 'availability', 'performance', or 'quality'
        recent_days: Length of the recent period in days (default 7)
        prior_days: Length of the prior period in days (default 7)

    Returns:
        Two-row list [period_a, period_b], or TERMINAL string if no data.
    """
    data = ch.compare_periods_metric(station_id, metric, recent_days, prior_days)
    if not data:
        return (
            f"TERMINAL: No OEE data for station '{station_id}' "
            f"(metric={metric}, recent_days={recent_days}, prior_days={prior_days}). "
            "Verify the station_id. Do not retry."
        )
    return data


def compare_stations(
    stage: Literal["STP", "WLD", "PNT", "ASM", "QAT"],
    metric: Literal["oee", "availability", "performance", "quality", "cycle_time"] = "oee",
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of OEE history (1–365; ignored for cycle_time)")] = 30,
) -> list[dict] | str:
    """[ACTION]: Compare a metric across all stations in a stage, ranked best to worst. [TARGET]: oee_metrics (ClickHouse) for OEE metrics; factory model for cycle_time.

    [INPUT PREREQUISITE]: stage must be one of the Literal stage codes. For metric='cycle_time',
    no days_back is needed (static design data). For OEE metrics, days_back is anchored to
    latest ClickHouse record.

    [OUTPUT GUARANTEE]: For OEE metrics: returns one row per station with station_id, avg_value,
    min_value, max_value, data_points — sorted descending (best first). For metric='cycle_time':
    returns station_id and ideal_cycle_time_sec sorted descending (longest = bottleneck station).

    [NEGATIVE BOUNDARY]: Cannot compare stations across different stages. Cannot return
    individual-day detail — use get_oee_metrics per station for that.

    Args:
        stage: Stage code: 'STP', 'WLD', 'PNT', 'ASM', or 'QAT'
        metric: Metric to compare; 'cycle_time' returns static design targets
        days_back: Days of OEE history (ignored for cycle_time)

    Returns:
        List of per-station dicts sorted best-first, or TERMINAL string if no data.
    """
    if metric == "cycle_time":
        from src.datagen.factory_model import FACTORY_STATIONS
        results = [
            {"station_id": sid, "ideal_cycle_time_sec": st.cycle_time_sec}
            for sid, st in FACTORY_STATIONS.items()
            if sid.startswith(stage)
        ]
        results.sort(key=lambda x: x["ideal_cycle_time_sec"], reverse=True)
        if not results:
            return (
                f"TERMINAL: No stations found for stage '{stage}'. "
                "Valid stages: STP, WLD, PNT, ASM, QAT. Do not retry."
            )
        return results

    data = ch.compare_stations_metric(stage, metric, days_back)
    if not data:
        return (
            f"TERMINAL: No OEE data for stage '{stage}' stations "
            f"(metric={metric}, days_back={days_back}). "
            "Verify the stage code. Do not retry."
        )
    return data
