"""Sensor telemetry generator — borrows distributions from AI4I 2020 dataset."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.datagen.factory_model import FACTORY_MACHINES, MachineSpec, SensorSpec
from src.datagen.generators.base import BaseGenerator


class TelemetryGenerator(BaseGenerator):
    """Generates sensor_readings for ClickHouse.

    Each machine has sensors defined by its type. Readings are generated at
    1-minute intervals with realistic noise, shift-dependent patterns, and
    occasional anomalies.
    """

    def __init__(
        self,
        days: int = 180,
        seed: int = 42,
        start_date: datetime | None = None,
        interval_seconds: int = 60,
        anomaly_rate: float = 0.005,
    ) -> None:
        """Initialize with sampling interval and anomaly injection rate."""
        super().__init__(days, seed, start_date)
        self.interval_seconds = interval_seconds
        self.anomaly_rate = anomaly_rate

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate sensor_readings rows for every machine in the factory."""
        readings: list[dict[str, Any]] = []

        for machine_id, machine in FACTORY_MACHINES.items():
            machine_readings = self._generate_machine_telemetry(machine)
            readings.extend(machine_readings)

        return {"sensor_readings": readings}

    def _generate_machine_telemetry(self, machine: MachineSpec) -> list[dict[str, Any]]:
        """Generate all sensor reading rows for a single machine across the simulation window."""
        rows: list[dict[str, Any]] = []
        n_points = (self.days * 86400) // self.interval_seconds

        for sensor in machine.sensors:
            values = self._generate_sensor_series(sensor, n_points, machine.machine_type)
            ts = self.start_date

            for i in range(n_points):
                rows.append({
                    "timestamp": ts,
                    "machine_id": machine.machine_id,
                    "station_id": machine.station_id,
                    "sensor_type": sensor.sensor_type,
                    "value": round(float(values[i]), 3),
                    "unit": sensor.unit,
                })
                ts += timedelta(seconds=self.interval_seconds)

        return rows

    def _generate_sensor_series(
        self, sensor: SensorSpec, n_points: int, machine_type: str
    ) -> np.ndarray:
        """Generate a realistic sensor time-series with patterns borrowed from AI4I."""
        mean = (sensor.min_normal + sensor.max_normal) / 2
        std = (sensor.max_normal - sensor.min_normal) / 6  # 99.7% within normal range

        # Base signal: random walk around mean (AI4I-style correlated noise)
        base = np.zeros(n_points)
        base[0] = mean
        walk_std = std * 0.1
        for i in range(1, n_points):
            base[i] = base[i - 1] + self.rng.normal(0, walk_std)
            # Mean reversion
            base[i] += (mean - base[i]) * 0.01

        # Add shift-dependent pattern (day shift slightly higher due to ambient temp)
        shift_pattern = np.zeros(n_points)
        points_per_day = 86400 // self.interval_seconds
        for i in range(n_points):
            hour = (i * self.interval_seconds // 3600) % 24
            if sensor.sensor_type == "TMP":
                shift_pattern[i] = 2.0 * np.sin(2 * np.pi * hour / 24)
            elif sensor.sensor_type == "PWR":
                # Higher power during day shift
                if 6 <= hour < 22:
                    shift_pattern[i] = std * 0.3
                else:
                    shift_pattern[i] = -std * 0.2

        # Add measurement noise
        noise = self.rng.normal(0, std * 0.15, n_points)

        values = base + shift_pattern + noise

        # Inject anomalies
        n_anomalies = int(n_points * self.anomaly_rate)
        if n_anomalies > 0:
            anomaly_indices = self.rng.choice(n_points, n_anomalies, replace=False)
            for idx in anomaly_indices:
                # Spike toward critical range
                direction = self.rng.choice([-1, 1])
                if direction > 0:
                    values[idx] = self.rng.uniform(sensor.max_normal, sensor.max_critical)
                else:
                    values[idx] = self.rng.uniform(sensor.min_critical, sensor.min_normal)

        # Clip to critical bounds
        values = np.clip(values, sensor.min_critical, sensor.max_critical)

        return values
