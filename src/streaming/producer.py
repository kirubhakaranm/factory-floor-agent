"""Kafka producer — publishes sensor readings and production events."""

import logging
from confluent_kafka import Producer

from src.config.settings import settings
from src.streaming.topics import (
    TOPIC_ALERTS_NEW,
    TOPIC_PRODUCTION_EVENTS,
    TOPIC_SENSORS_RAW,
    AlertMessage,
    ProductionEventMessage,
    SensorMessage,
)

logger = logging.getLogger("primeev.streaming.producer")

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": "primeev-factory-producer",
            "acks": "all",
            "linger.ms": 10,
            "batch.size": 16384,
        })
    return _producer


def _delivery_callback(err, msg) -> None:
    if err:
        logger.error("Message delivery failed", extra={"error": str(err), "topic": msg.topic()})


def publish_sensor_reading(message: SensorMessage) -> None:
    """Publish a sensor reading to Kafka."""
    producer = get_producer()
    producer.produce(
        topic=TOPIC_SENSORS_RAW,
        key=message.machine_id.encode("utf-8"),
        value=message.to_json(),
        callback=_delivery_callback,
    )


def publish_alert(message: AlertMessage) -> None:
    """Publish an alert to Kafka."""
    producer = get_producer()
    producer.produce(
        topic=TOPIC_ALERTS_NEW,
        key=message.machine_id.encode("utf-8"),
        value=message.to_json(),
        callback=_delivery_callback,
    )


def publish_production_event(message: ProductionEventMessage) -> None:
    """Publish a production event to Kafka."""
    producer = get_producer()
    producer.produce(
        topic=TOPIC_PRODUCTION_EVENTS,
        key=message.station_id.encode("utf-8"),
        value=message.to_json(),
        callback=_delivery_callback,
    )


def flush(timeout: float = 5.0) -> int:
    """Flush all pending messages. Returns number of messages still in queue."""
    producer = get_producer()
    return producer.flush(timeout)
