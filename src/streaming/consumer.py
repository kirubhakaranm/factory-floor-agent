"""Kafka consumer — reads sensor events, writes to ClickHouse, triggers alerts."""

import logging
import uuid
from datetime import datetime

from confluent_kafka import Consumer, KafkaError

from src.config.constants import SENSOR_RANGES
from src.config.settings import settings
from src.datagen.factory_model import FACTORY_MACHINES
from src.streaming.producer import publish_alert
from src.streaming.topics import (
    TOPIC_ALERTS_NEW,
    TOPIC_SENSORS_RAW,
    AlertMessage,
    SensorMessage,
)

logger = logging.getLogger("primeev.streaming.consumer")


def create_consumer(group_id: str = "primeev-factory-consumer") -> Consumer:
    return Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
    })


def check_alert_threshold(message: SensorMessage) -> AlertMessage | None:
    """Check if a sensor reading exceeds alert thresholds."""
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
            message=f"{message.sensor_type} reading {message.value:.2f} exceeds upper limit {max_normal:.2f}",
            timestamp=message.timestamp,
        )
    elif message.value < min_normal:
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
            message=f"{message.sensor_type} reading {message.value:.2f} below lower limit {min_normal:.2f}",
            timestamp=message.timestamp,
        )

    return None


def run_consumer(write_to_clickhouse: bool = True, max_messages: int | None = None) -> None:
    """Main consumer loop — reads sensor events, checks thresholds, writes to ClickHouse.

    Args:
        write_to_clickhouse: Whether to write sensor data to ClickHouse
        max_messages: Stop after this many messages (None = run forever)
    """
    consumer = create_consumer()
    consumer.subscribe([TOPIC_SENSORS_RAW])

    clickhouse_buffer: list[dict] = []
    buffer_size = 1000
    message_count = 0

    logger.info("Consumer started, subscribed to %s", TOPIC_SENSORS_RAW)

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

            sensor_msg = SensorMessage.from_json(msg.value())
            message_count += 1

            # Check alert thresholds
            alert = check_alert_threshold(sensor_msg)
            if alert:
                publish_alert(alert)
                logger.info(
                    "Alert triggered: %s on %s (%s=%.2f, threshold=%.2f)",
                    alert.severity, alert.machine_id, alert.sensor_type,
                    alert.sensor_value, alert.threshold,
                )

            # Buffer for ClickHouse batch insert
            if write_to_clickhouse:
                clickhouse_buffer.append({
                    "timestamp": sensor_msg.timestamp,
                    "machine_id": sensor_msg.machine_id,
                    "station_id": sensor_msg.station_id,
                    "sensor_type": sensor_msg.sensor_type,
                    "value": sensor_msg.value,
                    "unit": sensor_msg.unit,
                })

                if len(clickhouse_buffer) >= buffer_size:
                    _flush_to_clickhouse(clickhouse_buffer)
                    clickhouse_buffer.clear()

            if max_messages and message_count >= max_messages:
                break

    except KeyboardInterrupt:
        logger.info("Consumer interrupted")
    finally:
        if clickhouse_buffer and write_to_clickhouse:
            _flush_to_clickhouse(clickhouse_buffer)
        consumer.close()
        logger.info("Consumer stopped after %d messages", message_count)


def _flush_to_clickhouse(buffer: list[dict]) -> None:
    """Batch insert sensor readings into ClickHouse."""
    try:
        from src.db.clickhouse.client import get_clickhouse_client

        client = get_clickhouse_client()
        columns = ["timestamp", "machine_id", "station_id", "sensor_type", "value", "unit"]
        rows = [[row[col] for col in columns] for row in buffer]
        client.insert("sensor_readings", rows, column_names=columns)
        logger.info("Flushed %d readings to ClickHouse", len(buffer))
    except Exception as e:
        logger.error("Failed to flush to ClickHouse: %s", e)
