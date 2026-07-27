"""Kafka consumer — reads sensor events, writes to ClickHouse, calculates rolling Cpk, triggers alerts."""

import argparse
import logging
import statistics
import uuid
from collections import defaultdict, deque
from datetime import datetime

from confluent_kafka import Consumer, KafkaError

from src.config.constants import SENSOR_RANGES
from src.config.settings import settings
from src.datagen.factory_model import FACTORY_MACHINES
from src.streaming.producer import flush, publish_alert
from src.streaming.topics import (
    TOPIC_PRODUCTION_EVENTS,
    TOPIC_SENSORS_RAW,
    AlertMessage,
    ProductionEventMessage,
    SensorMessage,
)

logger = logging.getLogger("primeev.streaming.consumer")

# ── Rolling Cpk configuration ──────────────────────────────────────────────────
_CPK_WINDOW_SIZE = 30      # readings per sliding window per (station_id, sensor_type)
_CPK_BUFFER_SIZE = 50      # flush to ClickHouse every N Cpk records
_CPK_CRITICAL = 1.0        # Cpk below this → critical alert
_CPK_WARN = 1.33           # Cpk below this → trending_alert flag

# State: per (station_id, sensor_type) rolling window
_cpk_windows: dict[tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=_CPK_WINDOW_SIZE))


def create_consumer(group_id: str = "primeev-factory-consumer") -> Consumer:
    """Create and configure a Kafka consumer with the given consumer group ID."""
    return Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
    })


# ── Alert threshold check ──────────────────────────────────────────────────────

def check_alert_threshold(message: SensorMessage) -> AlertMessage | None:
    """Return an AlertMessage if the reading exceeds normal operating limits."""
    machine = FACTORY_MACHINES.get(message.machine_id)
    if not machine:
        return None

    ranges = SENSOR_RANGES.get(machine.machine_type, {})
    sensor_range = ranges.get(message.sensor_type)
    if not sensor_range:
        return None

    min_normal, max_normal, min_critical, max_critical = sensor_range

    if message.value > max_normal:
        severity = "critical" if message.value > max_critical * 0.95 else "major"
        return AlertMessage(
            alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
            machine_id=message.machine_id,
            station_id=message.station_id,
            alert_type="high_value",
            severity=severity,
            sensor_type=message.sensor_type,
            sensor_value=message.value,
            threshold=max_normal,
            message=(
                f"{message.sensor_type} reading {message.value:.2f} "
                f"exceeds upper limit {max_normal:.2f}"
            ),
            timestamp=message.timestamp,
        )
    if message.value < min_normal:
        severity = "critical" if message.value < min_critical * 1.05 else "major"
        return AlertMessage(
            alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
            machine_id=message.machine_id,
            station_id=message.station_id,
            alert_type="low_value",
            severity=severity,
            sensor_type=message.sensor_type,
            sensor_value=message.value,
            threshold=min_normal,
            message=(
                f"{message.sensor_type} reading {message.value:.2f} "
                f"below lower limit {min_normal:.2f}"
            ),
            timestamp=message.timestamp,
        )
    return None


# ── Rolling Cpk ────────────────────────────────────────────────────────────────

def update_rolling_cpk(message: SensorMessage) -> dict | None:
    """Add reading to per-(station, sensor_type) window; return Cpk record when full.

    Uses SENSOR_RANGES (min_normal, max_normal) as LSL/USL spec limits.
    Returns None until the window contains _CPK_WINDOW_SIZE readings.
    """
    machine = FACTORY_MACHINES.get(message.machine_id)
    if not machine:
        return None

    ranges = SENSOR_RANGES.get(machine.machine_type, {})
    sensor_range = ranges.get(message.sensor_type)
    if not sensor_range:
        return None

    lsl, usl = float(sensor_range[0]), float(sensor_range[1])
    key = (message.station_id, message.sensor_type)
    window = _cpk_windows[key]
    window.append(message.value)

    if len(window) < _CPK_WINDOW_SIZE:
        return None

    values = list(window)
    mean = statistics.mean(values)
    try:
        sigma = statistics.stdev(values)
    except statistics.StatisticsError:
        return None

    if sigma < 1e-9:
        return None

    cpu = (usl - mean) / (3 * sigma)
    cpl = (mean - lsl) / (3 * sigma)
    cpk = min(cpu, cpl)
    cp = (usl - lsl) / (6 * sigma)

    out_of_control = sum(1 for v in values if v > usl or v < lsl)

    return {
        "timestamp": message.timestamp,
        "station_id": message.station_id,
        "parameter": message.sensor_type,
        "cp": round(cp, 4),
        "cpk": round(cpk, 4),
        "pp": round(cp, 4),   # for stable process pp ≈ cp
        "ppk": round(cpk, 4),  # for stable process ppk ≈ cpk
        "out_of_control_signals": out_of_control,
        "trending_alert": 1 if cpk < _CPK_WARN else 0,
    }


def _make_cpk_alert(cpk_record: dict) -> AlertMessage | None:
    """Generate a Kafka alert when Cpk drops below the critical threshold."""
    cpk = cpk_record["cpk"]
    if cpk >= _CPK_CRITICAL:
        return None
    severity = "critical" if cpk < 0.67 else "major"
    station_id = cpk_record["station_id"]
    sensor_type = cpk_record["parameter"]
    return AlertMessage(
        alert_id=f"CPK-{uuid.uuid4().hex[:8]}",
        machine_id="",
        station_id=station_id,
        alert_type="cpk_breach",
        severity=severity,
        sensor_type=sensor_type,
        sensor_value=cpk,
        threshold=_CPK_CRITICAL,
        message=(
            f"Cpk={cpk:.3f} for {sensor_type} at {station_id} — "
            f"process incapable (threshold {_CPK_CRITICAL})"
        ),
        timestamp=cpk_record["timestamp"],
    )


# ── Production event handler ───────────────────────────────────────────────────

def handle_production_event(message: ProductionEventMessage) -> None:
    """Log a received production lifecycle event at INFO level."""
    logger.info(
        "Production event: %s | station=%s | batch=%s | status=%s",
        message.event_type,
        message.station_id,
        message.batch_id or "-",
        message.status or "-",
    )


# ── ClickHouse writers ─────────────────────────────────────────────────────────

def _flush_sensors_to_clickhouse(buffer: list[dict]) -> None:
    """Bulk-insert buffered sensor reading dicts into the ClickHouse sensor_readings table."""
    try:
        from src.db.clickhouse.client import insert_dataframe
        columns = ["timestamp", "machine_id", "station_id", "sensor_type", "value", "unit"]
        insert_dataframe("primeev_telemetry.sensor_readings", buffer, columns)
        logger.info("Flushed %d sensor readings to ClickHouse", len(buffer))
    except Exception as exc:
        logger.error("Sensor ClickHouse flush failed: %s", exc)


def _flush_cpk_to_clickhouse(buffer: list[dict]) -> None:
    """Bulk-insert buffered Cpk records into the ClickHouse process_capability_history table."""
    try:
        from src.db.clickhouse.client import insert_dataframe
        columns = [
            "timestamp", "station_id", "parameter",
            "cp", "cpk", "pp", "ppk",
            "out_of_control_signals", "trending_alert",
        ]
        # Convert ISO timestamp strings to datetime objects
        normalised = []
        for row in buffer:
            r = dict(row)
            ts = r.get("timestamp")
            if isinstance(ts, str):
                try:
                    r["timestamp"] = datetime.fromisoformat(ts)
                except ValueError:
                    r["timestamp"] = datetime.now()
            normalised.append(r)
        insert_dataframe("primeev_telemetry.process_capability_history", normalised, columns)
        logger.info("Flushed %d Cpk records to ClickHouse", len(buffer))
    except Exception as exc:
        logger.error("Cpk ClickHouse flush failed: %s", exc)


# ── Main consumer loop ─────────────────────────────────────────────────────────

def run_consumer(
    write_to_clickhouse: bool = True,
    compute_cpk: bool = True,
    max_messages: int | None = None,
) -> None:
    """Read sensor + production events, check thresholds, compute rolling Cpk, write to ClickHouse.

    Args:
        write_to_clickhouse: Write sensor data and Cpk records to ClickHouse.
        compute_cpk: Calculate rolling Cpk and publish alerts on breach.
        max_messages: Stop after N sensor messages (None = run forever).
    """
    consumer = create_consumer()
    consumer.subscribe([TOPIC_SENSORS_RAW, TOPIC_PRODUCTION_EVENTS])

    sensor_buffer: list[dict] = []
    cpk_buffer: list[dict] = []
    sensor_count = 0

    logger.info(
        "Consumer started | clickhouse=%s | cpk=%s",
        write_to_clickhouse, compute_cpk,
    )

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Consumer error: %s", msg.error())
                continue

            # ── Production events ─────────────────────────────────────────────
            if msg.topic() == TOPIC_PRODUCTION_EVENTS:
                try:
                    handle_production_event(ProductionEventMessage.from_json(msg.value()))
                except Exception as exc:
                    logger.warning("Bad production event: %s", exc)
                continue

            # ── Sensor readings ───────────────────────────────────────────────
            try:
                sensor_msg = SensorMessage.from_json(msg.value())
            except Exception as exc:
                logger.warning("Bad sensor message: %s", exc)
                continue

            sensor_count += 1

            # Threshold alert
            alert = check_alert_threshold(sensor_msg)
            if alert:
                publish_alert(alert)
                logger.info(
                    "Threshold alert: %s %s=%.2f on %s",
                    alert.severity, alert.sensor_type,
                    alert.sensor_value, alert.machine_id,
                )

            # Rolling Cpk
            if compute_cpk:
                cpk_record = update_rolling_cpk(sensor_msg)
                if cpk_record:
                    cpk_buffer.append(cpk_record)
                    logger.debug(
                        "Cpk: station=%s type=%s cpk=%.3f cp=%.3f ooc=%d",
                        cpk_record["station_id"], cpk_record["parameter"],
                        cpk_record["cpk"], cpk_record["cp"],
                        cpk_record["out_of_control_signals"],
                    )
                    cpk_alert = _make_cpk_alert(cpk_record)
                    if cpk_alert:
                        publish_alert(cpk_alert)
                        logger.warning(
                            "Cpk breach: %s at %s (Cpk=%.3f)",
                            cpk_alert.severity, cpk_alert.station_id,
                            cpk_alert.sensor_value,
                        )
                    if write_to_clickhouse and len(cpk_buffer) >= _CPK_BUFFER_SIZE:
                        _flush_cpk_to_clickhouse(cpk_buffer)
                        cpk_buffer.clear()

            # Sensor ClickHouse buffer
            if write_to_clickhouse:
                sensor_buffer.append({
                    "timestamp": sensor_msg.timestamp,
                    "machine_id": sensor_msg.machine_id,
                    "station_id": sensor_msg.station_id,
                    "sensor_type": sensor_msg.sensor_type,
                    "value": sensor_msg.value,
                    "unit": sensor_msg.unit,
                })
                if len(sensor_buffer) >= 1000:
                    _flush_sensors_to_clickhouse(sensor_buffer)
                    sensor_buffer.clear()

            if max_messages and sensor_count >= max_messages:
                break

    except KeyboardInterrupt:
        logger.info("Consumer interrupted")
    finally:
        if write_to_clickhouse:
            if sensor_buffer:
                _flush_sensors_to_clickhouse(sensor_buffer)
            if cpk_buffer:
                _flush_cpk_to_clickhouse(cpk_buffer)
        consumer.close()
        flush(timeout=5.0)
        logger.info("Consumer stopped after %d sensor messages", sensor_count)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="PrimeEV Factory Consumer")
    parser.add_argument("--no-clickhouse", action="store_true", help="Dry-run: skip ClickHouse writes")
    parser.add_argument("--no-cpk", action="store_true", help="Skip rolling Cpk computation")
    parser.add_argument("--max-messages", type=int, default=None, help="Stop after N sensor messages")
    args = parser.parse_args()

    run_consumer(
        write_to_clickhouse=not args.no_clickhouse,
        compute_cpk=not args.no_cpk,
        max_messages=args.max_messages,
    )
