-- PrimeEV Motors — ClickHouse schema initialization

CREATE DATABASE IF NOT EXISTS primeev_telemetry;

CREATE TABLE IF NOT EXISTS primeev_telemetry.sensor_readings
(
    timestamp DateTime64(3),
    machine_id String,
    station_id String,
    sensor_type String,
    value Float64,
    unit String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (station_id, machine_id, sensor_type, timestamp);

CREATE TABLE IF NOT EXISTS primeev_telemetry.energy_consumption
(
    timestamp DateTime64(3),
    station_id String,
    power_kw Float64,
    cumulative_kwh Float64,
    load_type String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (station_id, timestamp);

CREATE TABLE IF NOT EXISTS primeev_telemetry.oee_metrics
(
    timestamp DateTime,
    station_id String,
    shift String,
    availability Float64,
    performance Float64,
    quality Float64,
    oee Float64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (station_id, shift, timestamp);

CREATE TABLE IF NOT EXISTS primeev_telemetry.spc_measurements
(
    timestamp DateTime64(3),
    station_id String,
    parameter String,
    value Float64,
    ucl Float64,
    lcl Float64,
    usl Float64,
    lsl Float64,
    target Float64,
    cp Float64,
    cpk Float64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (station_id, parameter, timestamp);

CREATE TABLE IF NOT EXISTS primeev_telemetry.degradation_state
(
    timestamp DateTime,
    machine_id String,
    health_index Float64,
    rul_hours Float64,
    component String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (machine_id, component, timestamp);

CREATE TABLE IF NOT EXISTS primeev_telemetry.machine_reliability_metrics
(
    machine_id String,
    period String,
    period_start Date,
    mtbf_hrs Float64,
    mttr_hrs Float64,
    mttf_hrs Float64,
    availability_pct Float64,
    failure_rate Float64,
    total_downtime_hrs Float64,
    planned_downtime_hrs Float64,
    unplanned_downtime_hrs Float64,
    num_failures UInt32,
    num_repairs UInt32,
    total_repair_cost Float64,
    reliability_score Float64
)
ENGINE = MergeTree()
ORDER BY (machine_id, period, period_start);

CREATE TABLE IF NOT EXISTS primeev_telemetry.process_capability_history
(
    timestamp Date,
    station_id String,
    parameter String,
    cp Float64,
    cpk Float64,
    pp Float64,
    ppk Float64,
    out_of_control_signals UInt32,
    trending_alert UInt8
)
ENGINE = MergeTree()
ORDER BY (station_id, parameter, timestamp);

CREATE TABLE IF NOT EXISTS primeev_telemetry.agent_interactions
(
    timestamp DateTime64(3),
    interaction_id String,
    session_id String,
    sub_agent String,
    input_tokens UInt32,
    output_tokens UInt32,
    cache_read_tokens UInt32,
    cost_usd Float64,
    ttft_ms UInt32,
    total_latency_ms UInt32,
    tool_call_count UInt16,
    had_error UInt8,
    response_length_chars UInt32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (sub_agent, timestamp);
