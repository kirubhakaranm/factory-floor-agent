"""Degradation and RUL generator — inspired by C-MAPSS turbofan dataset patterns."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.datagen.factory_model import FACTORY_MACHINES, MachineSpec
from src.datagen.generators.base import BaseGenerator


class DegradationGenerator(BaseGenerator):
    """Generates degradation_state records for ClickHouse.

    Models piecewise degradation: healthy plateau followed by exponential decay.
    Each machine gets independent degradation curves with randomized onset and rate.
    Ground-truth RUL labels enable predictive agent evaluation.
    """

    def __init__(
        self,
        days: int = 180,
        seed: int = 42,
        start_date: datetime | None = None,
        sample_interval_hours: int = 1,
    ):
        super().__init__(days, seed, start_date)
        self.sample_interval_hours = sample_interval_hours

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        rows: list[dict[str, Any]] = []

        for machine_id, machine in FACTORY_MACHINES.items():
            components = self._get_degradation_components(machine.machine_type)
            for component in components:
                component_rows = self._generate_degradation_curve(machine, component)
                rows.extend(component_rows)

        return {"degradation_state": rows}

    def _get_degradation_components(self, machine_type: str) -> list[str]:
        components_by_type = {
            "HYP": ["hydraulic_pump", "seals", "hydraulic_fluid"],
            "SRV": ["servo_motor", "ball_screw", "encoder"],
            "RBT": ["joint_1_motor", "joint_2_motor", "reducer_gear", "wiring"],
            "OVN": ["heating_element", "insulation", "thermocouple"],
            "PMP": ["impeller", "mechanical_seal", "bearing"],
            "TST": ["load_cell", "sensor_array"],
            "CNC": ["spindle_bearing", "tool_holder", "coolant_pump"],
            "CNV": ["drive_belt", "roller_bearing", "motor"],
        }
        return components_by_type.get(machine_type, ["general"])

    def _generate_degradation_curve(
        self, machine: MachineSpec, component: str
    ) -> list[dict[str, Any]]:
        total_hours = self.days * 24
        n_samples = total_hours // self.sample_interval_hours

        # Randomized degradation parameters (C-MAPSS-inspired)
        # Healthy period: 40-80% of total time
        healthy_fraction = self.rng.uniform(0.4, 0.8)
        healthy_end = int(n_samples * healthy_fraction)

        # Degradation rate (exponential decay constant)
        decay_rate = self.rng.uniform(0.005, 0.03)

        # Generate health index (1.0 = perfect, 0.0 = failed)
        health = np.ones(n_samples)

        # Healthy phase: minor noise around 1.0
        health[:healthy_end] = 1.0 - self.rng.normal(0, 0.02, healthy_end).clip(0, 0.1)

        # Degradation phase: exponential decay
        for i in range(healthy_end, n_samples):
            t = i - healthy_end
            health[i] = health[healthy_end - 1] * np.exp(-decay_rate * t)

        health = np.clip(health, 0.0, 1.0)

        # Add measurement noise
        health += self.rng.normal(0, 0.01, n_samples)
        health = np.clip(health, 0.0, 1.0)

        # Calculate RUL (hours until health drops below 0.2 threshold)
        failure_threshold = 0.2
        failure_idx = n_samples  # default: doesn't fail in window
        for i in range(n_samples):
            if health[i] < failure_threshold:
                failure_idx = i
                break

        rows: list[dict[str, Any]] = []
        for i in range(n_samples):
            ts = self.start_date + timedelta(hours=i * self.sample_interval_hours)
            rul = max(0.0, (failure_idx - i) * self.sample_interval_hours)

            rows.append({
                "timestamp": ts,
                "machine_id": machine.machine_id,
                "health_index": round(float(health[i]), 4),
                "rul_hours": round(rul, 1),
                "component": component,
            })

        return rows
