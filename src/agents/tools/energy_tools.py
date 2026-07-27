"""Energy consumption tools."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.clickhouse import queries as ch


def get_energy_consumption(
    station_id: str,
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of history (1–365)")] = 7,
    granularity: Literal["minute", "hour", "day"] = "hour",
) -> list[dict] | str:
    """[ACTION]: Retrieve energy consumption time-series for a station at a chosen granularity. [TARGET]: energy_consumption table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'PNT-02-PRM').
    granularity must be one of the Literal values. Use 'day' for trend analysis;
    'hour' for daily patterns; 'minute' only when fine-grained spike detection is needed.

    [OUTPUT GUARANTEE]: Returns time-series rows with: ts (interval start), avg_power_kw,
    peak_power_kw, load_type. Ordered by ts ascending.

    [NEGATIVE BOUNDARY]: Cannot return energy data per machine — only per station.
    Cannot return cost figures — kWh × tariff must be computed externally.
    'minute' over days_back > 3 returns very large result sets.

    Args:
        station_id: Station identifier (e.g. 'PNT-02-PRM')
        days_back: Days of history (default 7)
        granularity: Time resolution: 'minute', 'hour', or 'day'

    Returns:
        List of energy time-series dicts. TERMINAL string if no data found.
    """
    data = ch.get_energy_consumption(station_id, days_back, granularity)
    if not data:
        return (
            f"TERMINAL: No energy data for station '{station_id}' "
            f"(granularity={granularity}, days_back={days_back}). "
            "Verify the station_id. Do not retry."
        )
    return data


def get_energy_trend(
    station_id: str,
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of history (1–365)")] = 30,
) -> dict | str:
    """[ACTION]: Summarize energy consumption trend for a station — average, peak, and direction. [TARGET]: energy_consumption table (ClickHouse), daily granularity.

    [INPUT PREREQUISITE]: station_id must be a valid station code. Uses daily granularity
    internally. Prefer this over get_energy_consumption for summary and trend queries.

    [OUTPUT GUARANTEE]: Returns a single dict with: station_id, days_analyzed, avg_power_kw,
    peak_power_kw, trend ('rising' if second half >5% above first half, 'falling' if >5% below,
    'stable' otherwise).

    [NEGATIVE BOUNDARY]: Cannot detect intra-day spikes — use get_energy_consumption with
    'hour' granularity for that. Cannot return per-machine energy breakdown.

    Args:
        station_id: Station identifier (e.g. 'PNT-02-PRM')
        days_back: Days of history (default 30)

    Returns:
        Trend summary dict, or TERMINAL string if no data.
    """
    data = ch.get_energy_consumption(station_id, days_back, granularity="day")
    if not data:
        return (
            f"TERMINAL: No energy data for station '{station_id}' (days_back={days_back}). "
            "Verify the station_id. Do not retry."
        )

    values = [d["avg_power_kw"] for d in data if d.get("avg_power_kw")]
    if not values:
        return (
            f"TERMINAL: Energy records for '{station_id}' contain no valid power readings. "
            "Do not retry — report that energy data is unavailable."
        )

    avg = sum(values) / len(values)
    peak = max(values)
    first_half = values[:len(values) // 2]
    second_half = values[len(values) // 2:]
    f_avg = sum(first_half) / len(first_half) if first_half else 0
    s_avg = sum(second_half) / len(second_half) if second_half else 0

    return {
        "station_id": station_id,
        "days_analyzed": len(values),
        "avg_power_kw": round(avg, 1),
        "peak_power_kw": round(peak, 1),
        "trend": "rising" if s_avg > f_avg * 1.05 else "falling" if s_avg < f_avg * 0.95 else "stable",
    }
