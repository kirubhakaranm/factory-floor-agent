"""Energy consumption generator — temporal patterns from Steel Industry Energy dataset."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.datagen.factory_model import ALL_STATION_IDS
from src.datagen.generators.base import BaseGenerator


class EnergyGenerator(BaseGenerator):
    """Generates energy_consumption records for ClickHouse.

    Patterns borrowed from Steel Industry Energy Consumption dataset:
    - Shift-dependent load profiles
    - Weekend reduction
    - Station-specific base loads
    """

    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None) -> None:
        """Initialize the energy generator with default window and seed."""
        super().__init__(days, seed, start_date)

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate energy_consumption rows at 15-minute intervals for all stations."""
        rows: list[dict[str, Any]] = []

        base_loads = {
            "STP-01-PRS": 95.0, "STP-02-PRS": 85.0, "STP-03-TRM": 55.0,
            "WLD-01-UBD": 70.0, "WLD-02-SDP": 65.0, "WLD-03-RCL": 60.0,
            "PNT-01-ECT": 40.0, "PNT-02-PRM": 50.0, "PNT-03-CLR": 120.0,
            "ASM-01-PWR": 45.0, "ASM-02-INT": 30.0, "ASM-03-FNL": 35.0,
            "QAT-01-ALN": 15.0, "QAT-02-WLT": 20.0, "QAT-03-DYN": 80.0,
        }

        for station_id in ALL_STATION_IDS:
            base = base_loads.get(station_id, 50.0)
            cumulative = 0.0

            # 15-minute intervals
            n_readings = self.days * 96  # 96 readings per day
            for i in range(n_readings):
                ts = self.start_date + timedelta(minutes=i * 15)
                hour = ts.hour

                # Shift pattern
                if 6 <= hour < 22:
                    load_factor = 1.0
                    load_type = "high" if 8 <= hour < 18 else "medium"
                else:
                    load_factor = 0.4
                    load_type = "low"

                # Weekend reduction
                if self.is_weekend(ts):
                    load_factor *= 0.35

                power = base * load_factor + self.rng.normal(0, base * 0.08)
                power = max(base * 0.1, power)

                kwh_increment = power * 0.25  # 15 min = 0.25 hours
                cumulative += kwh_increment

                rows.append({
                    "timestamp": ts,
                    "station_id": station_id,
                    "power_kw": round(float(power), 2),
                    "cumulative_kwh": round(cumulative, 2),
                    "load_type": load_type,
                })

        return {"energy_consumption": rows}
