"""Sensor data tools — fetch readings, trends, and current values from ClickHouse."""

from src.db.clickhouse import queries as ch


def fetch_sensor_data(
    machine_id: str,
    sensor_type: str,
    hours_back: int = 24,
    resolution_minutes: int = 5,
) -> list[dict]:
    """Fetch time-series sensor data for a specific machine and sensor type.

    Args:
        machine_id: Machine identifier (e.g., 'STP-01-PRS-HYP01')
        sensor_type: Sensor type code (TMP, VIB, PRS, TRQ, RPM, PWR, FLW, CUR, HUM)
        hours_back: How many hours of history to fetch (default 24)
        resolution_minutes: Aggregation interval in minutes (default 5)

    Returns:
        List of {ts, avg_value, min_value, max_value, std_value, unit}
    """
    return ch.get_sensor_trend(machine_id, sensor_type, hours_back, resolution_minutes)


def get_sensor_trend(
    machine_id: str,
    sensor_type: str,
    hours_back: int = 8,
) -> dict:
    """Get a summary of sensor trend including mean, min, max, standard deviation, and slope direction.

    Args:
        machine_id: Machine identifier
        sensor_type: Sensor type code
        hours_back: Hours of history to analyze

    Returns:
        Summary dict with trend statistics and direction (rising/falling/stable)
    """
    data = ch.get_sensor_trend(machine_id, sensor_type, hours_back, resolution_minutes=30)
    if not data:
        return {"error": f"No data found for {machine_id}:{sensor_type}"}

    values = [d["avg_value"] for d in data if d.get("avg_value") is not None]
    if len(values) < 2:
        return {"error": "Insufficient data points for trend analysis"}

    mean_val = sum(values) / len(values)
    min_val = min(values)
    max_val = max(values)

    first_half = values[:len(values) // 2]
    second_half = values[len(values) // 2:]
    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)

    if second_avg > first_avg * 1.02:
        direction = "rising"
    elif second_avg < first_avg * 0.98:
        direction = "falling"
    else:
        direction = "stable"

    return {
        "machine_id": machine_id,
        "sensor_type": sensor_type,
        "hours_back": hours_back,
        "mean": round(mean_val, 3),
        "min": round(min_val, 3),
        "max": round(max_val, 3),
        "range": round(max_val - min_val, 3),
        "data_points": len(values),
        "direction": direction,
        "unit": data[0].get("unit", ""),
        "first_half_avg": round(first_avg, 3),
        "second_half_avg": round(second_avg, 3),
    }


def get_current_readings(station_id: str) -> list[dict]:
    """Get the latest sensor readings for all machines at a station.

    Args:
        station_id: Station identifier (e.g., 'STP-01-PRS')

    Returns:
        List of {machine_id, sensor_type, latest_value, latest_time, unit}
    """
    return ch.get_current_readings(station_id)
