"""ClickHouse query builders for time-series, reliability, and SPC data."""

from src.db.clickhouse.client import query

# Use latest data timestamp as anchor so queries work on generated/historical datasets.
# In production with live streaming data, this naturally equals now().
_ANCHOR = {
    "sensor_readings": "(SELECT max(timestamp) FROM primeev_telemetry.sensor_readings)",
    "oee_metrics": "(SELECT max(timestamp) FROM primeev_telemetry.oee_metrics)",
    "energy_consumption": "(SELECT max(timestamp) FROM primeev_telemetry.energy_consumption)",
    "spc_measurements": "(SELECT max(timestamp) FROM primeev_telemetry.spc_measurements)",
    "process_capability_history": "(SELECT max(timestamp) FROM primeev_telemetry.process_capability_history)",
    "degradation_state": "(SELECT max(timestamp) FROM primeev_telemetry.degradation_state)",
}


def get_sensor_trend(
    machine_id: str,
    sensor_type: str,
    hours_back: int = 24,
    resolution_minutes: int = 5,
) -> list[dict]:
    """Get aggregated sensor trend for a machine."""
    anchor = _ANCHOR["sensor_readings"]
    return query(f"""
        SELECT
            toStartOfInterval(timestamp, INTERVAL {resolution_minutes} MINUTE) AS ts,
            avg(value) AS avg_value,
            min(value) AS min_value,
            max(value) AS max_value,
            stddevPop(value) AS std_value,
            any(unit) AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = '{machine_id}'
          AND sensor_type = '{sensor_type}'
          AND timestamp >= {anchor} - INTERVAL {hours_back} HOUR
        GROUP BY ts
        ORDER BY ts
    """)


def get_current_readings(station_id: str) -> list[dict]:
    """Get latest sensor reading for each machine/sensor at a station."""
    anchor = _ANCHOR["sensor_readings"]
    return query(f"""
        SELECT
            machine_id,
            sensor_type,
            argMax(value, timestamp) AS latest_value,
            max(timestamp) AS latest_time,
            any(unit) AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE station_id = '{station_id}'
          AND timestamp >= {anchor} - INTERVAL 2 HOUR
        GROUP BY machine_id, sensor_type
        ORDER BY machine_id, sensor_type
    """)


def get_oee_metrics(
    station_id: str,
    shift: str | None = None,
    days_back: int = 30,
) -> list[dict]:
    """Get OEE metrics for a station."""
    anchor = _ANCHOR["oee_metrics"]
    shift_filter = f"AND shift = '{shift}'" if shift else ""
    return query(f"""
        SELECT
            toDate(timestamp) AS date,
            shift,
            avg(availability) AS avg_availability,
            avg(performance) AS avg_performance,
            avg(quality) AS avg_quality,
            avg(oee) AS avg_oee
        FROM primeev_telemetry.oee_metrics
        WHERE station_id = '{station_id}'
          AND timestamp >= {anchor} - INTERVAL {days_back} DAY
          {shift_filter}
        GROUP BY date, shift
        ORDER BY date, shift
    """)


def get_energy_consumption(
    station_id: str,
    days_back: int = 7,
    granularity: str = "hour",
) -> list[dict]:
    """Get energy consumption for a station."""
    anchor = _ANCHOR["energy_consumption"]
    interval = {"minute": "1 MINUTE", "hour": "1 HOUR", "day": "1 DAY"}.get(granularity, "1 HOUR")
    return query(f"""
        SELECT
            toStartOfInterval(timestamp, INTERVAL {interval}) AS ts,
            avg(power_kw) AS avg_power_kw,
            max(power_kw) AS peak_power_kw,
            any(load_type) AS load_type
        FROM primeev_telemetry.energy_consumption
        WHERE station_id = '{station_id}'
          AND timestamp >= {anchor} - INTERVAL {days_back} DAY
        GROUP BY ts
        ORDER BY ts
    """)


def get_spc_data(
    station_id: str,
    parameter: str,
    days_back: int = 7,
) -> list[dict]:
    """Get SPC measurement data for control charts."""
    anchor = _ANCHOR["spc_measurements"]
    return query(f"""
        SELECT
            timestamp, value, ucl, lcl, usl, lsl, target, cp, cpk
        FROM primeev_telemetry.spc_measurements
        WHERE station_id = '{station_id}'
          AND parameter = '{parameter}'
          AND timestamp >= {anchor} - INTERVAL {days_back} DAY
        ORDER BY timestamp
        LIMIT 1000
    """)


def get_process_capability(
    station_id: str,
    parameter: str,
    days_back: int = 30,
) -> list[dict]:
    """Get daily Cpk trend."""
    anchor = _ANCHOR["process_capability_history"]
    return query(f"""
        SELECT
            timestamp AS date,
            cp, cpk, pp, ppk,
            out_of_control_signals,
            trending_alert
        FROM primeev_telemetry.process_capability_history
        WHERE station_id = '{station_id}'
          AND parameter = '{parameter}'
          AND timestamp >= {anchor} - INTERVAL {days_back} DAY
        ORDER BY timestamp
    """)


def get_reliability_metrics(
    machine_id: str,
    period: str = "monthly",
) -> list[dict]:
    """Get MTBF, MTTR, availability for a machine."""
    return query(f"""
        SELECT
            period_start,
            mtbf_hrs, mttr_hrs, mttf_hrs,
            availability_pct, failure_rate,
            total_downtime_hrs,
            planned_downtime_hrs, unplanned_downtime_hrs,
            num_failures, num_repairs,
            total_repair_cost, reliability_score
        FROM primeev_telemetry.machine_reliability_metrics
        WHERE machine_id = '{machine_id}'
          AND period = '{period}'
        ORDER BY period_start
    """)


def get_degradation_state(
    machine_id: str,
    component: str | None = None,
    hours_back: int = 168,
) -> list[dict]:
    """Get degradation / health index trend for a machine."""
    anchor = _ANCHOR["degradation_state"]
    comp_filter = f"AND component = '{component}'" if component else ""
    return query(f"""
        SELECT
            timestamp, component, health_index, rul_hours
        FROM primeev_telemetry.degradation_state
        WHERE machine_id = '{machine_id}'
          AND timestamp >= {anchor} - INTERVAL {hours_back} HOUR
          {comp_filter}
        ORDER BY timestamp
    """)


def compare_shifts(
    station_id: str,
    metric: str = "oee",
    days_back: int = 30,
) -> list[dict]:
    """Compare metrics across shifts for a station."""
    anchor = _ANCHOR["oee_metrics"]
    return query(f"""
        SELECT
            shift,
            avg({metric}) AS avg_value,
            min({metric}) AS min_value,
            max({metric}) AS max_value,
            count() AS data_points
        FROM primeev_telemetry.oee_metrics
        WHERE station_id = '{station_id}'
          AND timestamp >= {anchor} - INTERVAL {days_back} DAY
        GROUP BY shift
        ORDER BY shift
    """)
