"""Sensor data tools — fetch readings, trends, and current values from ClickHouse."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.clickhouse import queries as ch


def fetch_sensor_data(
    machine_id: str,
    sensor_type: Literal["TMP", "VIB", "PRS", "TRQ", "RPM", "PWR", "FLW", "CUR", "HUM"],
    hours_back: Annotated[int, Field(ge=1, le=720, description="Hours of history (1–720)")] = 24,
    resolution_minutes: Annotated[int, Field(ge=1, le=60, description="Aggregation interval in minutes (1–60)")] = 5,
) -> list[dict] | str:
    """[ACTION]: Fetch raw time-series sensor readings for a machine-sensor pair. [TARGET]: sensor_readings table (ClickHouse).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier (e.g. 'STP-01-PRS-HYP01').
    sensor_type must be one of the Literal values. Prefer get_sensor_trend for summarized analysis;
    use this only when raw time-series points are explicitly needed.

    [OUTPUT GUARANTEE]: Returns aggregated intervals with: ts, avg_value, min_value, max_value,
    std_value, unit. Each interval spans resolution_minutes. Ordered by ts ascending.

    [NEGATIVE BOUNDARY]: Cannot return sensor readings for machines not in ClickHouse.
    Cannot return readings outside the hours_back window. Does not compute trend direction —
    use get_sensor_trend for that.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')
        sensor_type: Sensor type: TMP, VIB, PRS, TRQ, RPM, PWR, FLW, CUR, or HUM
        hours_back: Hours of history (default 24)
        resolution_minutes: Aggregation interval in minutes (default 5)

    Returns:
        List of time-series dicts. TERMINAL string if no data found.
    """
    data = ch.get_sensor_trend(machine_id, sensor_type, hours_back, resolution_minutes)
    if not data:
        return (
            f"TERMINAL: No sensor readings found for {machine_id}:{sensor_type} "
            f"over the last {hours_back} hours. "
            "Verify machine_id and sensor_type are correct. Do not retry."
        )
    return data


def get_sensor_trend(
    machine_id: str,
    sensor_type: Literal["TMP", "VIB", "PRS", "TRQ", "RPM", "PWR", "FLW", "CUR", "HUM"] = "VIB",
    hours_back: Annotated[int, Field(ge=1, le=720, description="Hours of history to analyze (1–720)")] = 8,
) -> dict | str:
    """[ACTION]: Summarize sensor trend for a machine-sensor pair — mean, min, max, and direction. [TARGET]: sensor_readings table (ClickHouse).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier. sensor_type defaults to
    VIB (vibration) if not specified — call without sensor_type when the user hasn't specified one.
    Use this (not fetch_sensor_data) for any 'last N hours' trend query.

    [OUTPUT GUARANTEE]: Returns a single dict with: machine_id, sensor_type, hours_back,
    mean, min, max, range, data_points, direction ('rising'/'falling'/'stable'), unit,
    first_half_avg, second_half_avg. Direction is based on comparing first vs second half averages
    using a ±2% threshold.

    [NEGATIVE BOUNDARY]: Cannot compare multiple machines or sensor types in one call.
    Requires at least 2 data points; fewer returns TERMINAL string. Does not check against
    spec limits — use get_measurement_specs or search_specification for that.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')
        sensor_type: Sensor type: TMP, VIB, PRS, TRQ, RPM, PWR, FLW, CUR, or HUM
        hours_back: Hours of history to analyze (default 8)

    Returns:
        Trend summary dict, or TERMINAL string if insufficient data.
    """
    data = ch.get_sensor_trend(machine_id, sensor_type, hours_back, resolution_minutes=30)
    if not data:
        return (
            f"TERMINAL: No sensor data for {machine_id}:{sensor_type} "
            f"over the last {hours_back} hours. "
            "Verify machine_id and sensor_type. Do not retry."
        )

    values = [d["avg_value"] for d in data if d.get("avg_value") is not None]
    if len(values) < 2:
        return (
            f"TERMINAL: Insufficient data points for {machine_id}:{sensor_type} "
            f"({len(values)} point(s) found, minimum 2 required). "
            "Try increasing hours_back. Do not retry with same parameters."
        )

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


def get_current_readings(station_id: str) -> list[dict] | str:
    """[ACTION]: Retrieve the latest sensor value for every machine-sensor pair at a station. [TARGET]: sensor_readings table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'STP-01-PRS').
    Use this for 'current state' or 'what is the station reading right now?' queries.

    [OUTPUT GUARANTEE]: Returns one row per (machine_id, sensor_type) combination with:
    machine_id, sensor_type, latest_value, latest_time, unit. Covers the last 2 hours of data.

    [NEGATIVE BOUNDARY]: Cannot return historical trends — use get_sensor_trend for that.
    Cannot return readings for a single machine-sensor pair — use fetch_sensor_data for targeted queries.

    Args:
        station_id: Station identifier (e.g. 'STP-01-PRS')

    Returns:
        List of latest-reading dicts per sensor. TERMINAL string if station has no data.
    """
    data = ch.get_current_readings(station_id)
    if not data:
        return (
            f"TERMINAL: No current sensor readings for station '{station_id}'. "
            "Station may be offline or sensor data unavailable. Do not retry."
        )
    return data
