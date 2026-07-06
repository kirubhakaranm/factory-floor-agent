"""Factory simulator — replays generated sensor data as a live Kafka stream."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from src.datagen.factory_model import FACTORY_MACHINES
from src.streaming.producer import flush, publish_sensor_reading
from src.streaming.topics import SensorMessage

logger = logging.getLogger("primeev.streaming.simulator")


def run_simulator(
    data_dir: str = "data",
    speed_multiplier: float = 1.0,
    max_messages: int | None = None,
) -> None:
    """Replay generated sensor data as a live Kafka stream.

    Args:
        data_dir: Directory containing generated JSON data files
        speed_multiplier: Playback speed (1.0 = real-time, 10.0 = 10x faster, 0 = as fast as possible)
        max_messages: Stop after this many messages (None = replay entire file)
    """
    sensor_file = Path(data_dir) / "sensor_readings.json"
    if not sensor_file.exists():
        logger.error("No sensor data found at %s. Run 'python -m src.datagen.cli generate' first.", sensor_file)
        return

    logger.info("Loading sensor data from %s...", sensor_file)
    with open(sensor_file) as f:
        readings = json.load(f)
    logger.info("Loaded %d sensor readings", len(readings))

    if not readings:
        return

    message_count = 0
    last_ts = None
    start_time = time.time()

    logger.info(
        "Starting simulator: speed=%.1fx, max_messages=%s",
        speed_multiplier, max_messages or "unlimited",
    )

    try:
        for reading in readings:
            msg = SensorMessage(
                machine_id=reading["machine_id"],
                station_id=reading["station_id"],
                sensor_type=reading["sensor_type"],
                value=reading["value"],
                unit=reading["unit"],
                timestamp=reading["timestamp"],
            )

            publish_sensor_reading(msg)
            message_count += 1

            # Throttle to simulate real-time
            if speed_multiplier > 0 and last_ts and reading.get("timestamp"):
                try:
                    current_ts = datetime.fromisoformat(reading["timestamp"])
                    prev_ts = datetime.fromisoformat(last_ts)
                    delta = (current_ts - prev_ts).total_seconds()
                    if delta > 0:
                        time.sleep(delta / speed_multiplier)
                except (ValueError, TypeError):
                    pass

            last_ts = reading.get("timestamp")

            # Periodic flush and logging
            if message_count % 1000 == 0:
                flush(timeout=2.0)
                elapsed = time.time() - start_time
                rate = message_count / elapsed if elapsed > 0 else 0
                logger.info(
                    "Published %d messages (%.0f msg/sec)",
                    message_count, rate,
                )

            if max_messages and message_count >= max_messages:
                break

    except KeyboardInterrupt:
        logger.info("Simulator interrupted")
    finally:
        remaining = flush(timeout=10.0)
        elapsed = time.time() - start_time
        logger.info(
            "Simulator complete: %d messages in %.1f sec (%.0f msg/sec), %d unflushed",
            message_count, elapsed, message_count / max(elapsed, 0.001), remaining,
        )


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="PrimeEV Factory Simulator")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument("--speed", type=float, default=100.0, help="Speed multiplier (default: 100x)")
    parser.add_argument("--max-messages", type=int, default=None, help="Max messages to send")

    args = parser.parse_args()
    run_simulator(args.data_dir, args.speed, args.max_messages)
