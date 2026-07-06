"""Energy consumption tools."""

from src.db.clickhouse import queries as ch


def get_energy_consumption(
    station_id: str,
    days_back: int = 7,
    granularity: str = "hour",
) -> list[dict]:
    """Get energy consumption data for a station.

    Args:
        station_id: Station identifier
        days_back: Days of history
        granularity: Time granularity: 'minute', 'hour', or 'day'

    Returns:
        Time-series of avg_power_kw, peak_power_kw, load_type
    """
    return ch.get_energy_consumption(station_id, days_back, granularity)


def get_energy_trend(station_id: str, days_back: int = 30) -> dict:
    """Get energy consumption trend summary for a station.

    Args:
        station_id: Station identifier
        days_back: Days of history

    Returns:
        Summary with avg daily consumption, peak, trend direction, anomalies
    """
    data = ch.get_energy_consumption(station_id, days_back, granularity="day")
    if not data:
        return {"error": f"No energy data for {station_id}"}

    values = [d["avg_power_kw"] for d in data if d.get("avg_power_kw")]
    if not values:
        return {"error": "No valid readings"}

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
