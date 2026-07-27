"""Equipment failure generator — 5 failure modes from AI4I 2020 + MTBF/MTTR metrics."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.config.constants import (
    FAILURE_DETECTED_BY,
    FAILURE_MODES,
    FAILURE_SEVERITIES,
    generate_failure_id,
    generate_work_order_id,
)
from src.datagen.factory_model import FACTORY_MACHINES, MachineSpec
from src.datagen.generators.base import BaseGenerator


class FailureGenerator(BaseGenerator):
    """Generates equipment_failures and maintenance_history for Postgres,
    and machine_reliability_metrics for ClickHouse.

    Failure modes use AI4I 2020 logic:
    - TWF: tool_wear > threshold
    - HDF: temperature differential too high
    - PWF: power (torque × speed) out of range
    - OSF: torque × tool_wear exceeds limit
    - RNF: 0.1% random chance
    """

    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None) -> None:
        """Initialize failure generator with sequence counters for IDs."""
        super().__init__(days, seed, start_date)
        self._failure_seq: dict[str, int] = {}
        self._wo_seq = 0

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate equipment_failures, maintenance_history, work_orders, and reliability metrics."""
        failures: list[dict[str, Any]] = []
        maintenance: list[dict[str, Any]] = []
        work_orders: list[dict[str, Any]] = []

        for machine_id, machine in FACTORY_MACHINES.items():
            m_failures, m_maintenance, m_work_orders = self._generate_machine_failures(machine)
            failures.extend(m_failures)
            maintenance.extend(m_maintenance)
            work_orders.extend(m_work_orders)

        reliability = self._calculate_reliability_metrics(failures)

        return {
            "equipment_failures": failures,
            "maintenance_history": maintenance,
            "work_orders": work_orders,
            "machine_reliability_metrics": reliability,
        }

    def _generate_machine_failures(
        self, machine: MachineSpec
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Generate failure events, maintenance records, and work orders for a single machine."""
        failures = []
        maintenance = []
        work_orders = []

        # Failure rate depends on criticality and machine type
        # Targets: ~1-3 failures/machine/month for high-use types, fewer for TST/CNV
        base_rate_per_day = {
            "HYP": 0.050, "SRV": 0.035, "RBT": 0.030, "OVN": 0.040,
            "PMP": 0.055, "TST": 0.015, "CNC": 0.040, "CNV": 0.012,
        }
        rate = base_rate_per_day.get(machine.machine_type, 0.025)
        if machine.criticality == "A":
            rate *= 0.6  # better maintained — fewer failures
        elif machine.criticality == "C":
            rate *= 1.4

        # Generate preventive maintenance events
        pm_interval_days = machine.maintenance_interval_hrs / 24
        pm_day = pm_interval_days
        while pm_day < self.days:
            pm_date = self.start_date + timedelta(days=pm_day)
            self._wo_seq += 1
            wo_id = generate_work_order_id(pm_date.year, pm_date.month, self._wo_seq)
            duration_min = self.rng.integers(30, 120)

            work_orders.append({
                "wo_id": wo_id,
                "machine_id": machine.machine_id,
                "type": "preventive",
                "priority": "medium",
                "description": f"Scheduled PM for {machine.model}",
                "assigned_to": f"TECH-{self.rng.integers(1, 13):03d}",
                "status": "completed",
                "created_at": pm_date - timedelta(days=7),
                "completed_at": pm_date,
            })

            maintenance.append({
                "machine_id": machine.machine_id,
                "type": "preventive",
                "trigger": "scheduled",
                "started_at": pm_date,
                "completed_at": pm_date + timedelta(minutes=int(duration_min)),
                "duration_min": int(duration_min),
                "technician_id": f"TECH-{self.rng.integers(1, 13):03d}",
                "parts_replaced": self._random_parts(machine.machine_type),
                "labor_hours": round(duration_min / 60, 1),
                "total_cost": round(float(self.rng.uniform(200, 1500)), 2),
                "machine_condition_before": int(self.rng.integers(5, 8)),
                "machine_condition_after": int(self.rng.integers(8, 10)),
                "wo_id": wo_id,
            })

            pm_day += pm_interval_days

        # Generate random failures
        for day in range(self.days):
            if self.rng.random() < rate:
                failure_date = self.start_date + timedelta(
                    days=day, hours=int(self.rng.integers(0, 24))
                )
                failure_mode = self.rng.choice(list(FAILURE_MODES.keys()))
                severity = self._get_severity(failure_mode)
                downtime = self._get_downtime(severity)
                component = self._get_failed_component(machine.machine_type, failure_mode)

                station_short = machine.station_id.replace("-", "")[:5]
                if station_short not in self._failure_seq:
                    self._failure_seq[station_short] = 0
                self._failure_seq[station_short] += 1

                failure_id = generate_failure_id(
                    machine.station_id,
                    failure_date.year,
                    failure_date.month,
                    self._failure_seq[station_short],
                )

                self._wo_seq += 1
                wo_id = generate_work_order_id(
                    failure_date.year, failure_date.month, self._wo_seq
                )

                repair_cost_parts = round(float(self.rng.uniform(100, 5000)), 2)
                repair_cost_labor = round(float(downtime / 60 * 85), 2)  # $85/hr
                lost_production = int(downtime / 5)  # ~1 unit per 5 min

                failures.append({
                    "failure_id": failure_id,
                    "machine_id": machine.machine_id,
                    "vin_id": None,
                    "failure_mode": failure_mode,
                    "failure_type": FAILURE_MODES[failure_mode],
                    "component_failed": component,
                    "severity": severity,
                    "detected_by": self.rng.choice(FAILURE_DETECTED_BY),
                    "failure_start": failure_date,
                    "failure_end": failure_date + timedelta(minutes=int(downtime)),
                    "downtime_min": int(downtime),
                    "production_units_lost": lost_production,
                    "root_cause": self._get_root_cause(failure_mode, component),
                    "corrective_action": f"Replaced {component}",
                    "preventive_action": f"Increase inspection frequency for {component}",
                    "cost_parts": repair_cost_parts,
                    "cost_labor": repair_cost_labor,
                    "cost_lost_production": round(lost_production * 250.0, 2),
                    "linked_wo_id": wo_id,
                })

                work_orders.append({
                    "wo_id": wo_id,
                    "machine_id": machine.machine_id,
                    "type": "corrective",
                    "priority": "high" if severity == "critical" else "medium",
                    "description": f"{FAILURE_MODES[failure_mode]} on {machine.model} — {component}",
                    "assigned_to": f"TECH-{self.rng.integers(1, 13):03d}",
                    "status": "completed",
                    "created_at": failure_date,
                    "completed_at": failure_date + timedelta(minutes=int(downtime)),
                })

                maintenance.append({
                    "machine_id": machine.machine_id,
                    "type": "corrective",
                    "trigger": "breakdown",
                    "started_at": failure_date,
                    "completed_at": failure_date + timedelta(minutes=int(downtime)),
                    "duration_min": int(downtime),
                    "technician_id": f"TECH-{self.rng.integers(1, 13):03d}",
                    "parts_replaced": [component],
                    "labor_hours": round(downtime / 60, 1),
                    "total_cost": round(repair_cost_parts + repair_cost_labor, 2),
                    "machine_condition_before": int(self.rng.integers(1, 4)),
                    "machine_condition_after": int(self.rng.integers(7, 10)),
                    "wo_id": wo_id,
                })

        return failures, maintenance, work_orders

    def _get_severity(self, failure_mode: str) -> str:
        """Sample a severity level (critical/major/minor) weighted by failure mode."""
        weights = {
            "TWF": [0.1, 0.6, 0.3],
            "HDF": [0.3, 0.5, 0.2],
            "PWF": [0.4, 0.4, 0.2],
            "OSF": [0.5, 0.4, 0.1],
            "RNF": [0.2, 0.5, 0.3],
        }
        return self.rng.choice(FAILURE_SEVERITIES, p=weights.get(failure_mode, [0.3, 0.4, 0.3]))

    def _get_downtime(self, severity: str) -> float:
        """Return a random downtime duration in minutes for the given severity level."""
        ranges = {"critical": (120, 480), "major": (30, 180), "minor": (10, 60)}
        lo, hi = ranges.get(severity, (30, 120))
        return float(self.rng.integers(lo, hi + 1))

    def _get_failed_component(self, machine_type: str, failure_mode: str) -> str:
        """Return a randomly selected failed component name for the machine type."""
        components = {
            "HYP": ["hydraulic pump", "pressure relief valve", "cylinder seal", "solenoid valve"],
            "SRV": ["servo motor", "encoder", "ball screw", "brake module"],
            "RBT": ["joint motor", "reducer gear", "teach pendant", "cable harness"],
            "OVN": ["heating element", "thermocouple", "fan motor", "door seal"],
            "PMP": ["impeller", "mechanical seal", "bearing", "coupling"],
            "TST": ["load cell", "sensor", "calibration module", "data logger"],
            "CNC": ["spindle bearing", "tool holder", "coolant pump", "way cover"],
            "CNV": ["drive belt", "roller bearing", "motor", "chain link"],
        }
        options = components.get(machine_type, ["general component"])
        return self.rng.choice(options)

    def _get_root_cause(self, failure_mode: str, component: str) -> str:
        """Return a human-readable root cause description for the failure mode and component."""
        causes = {
            "TWF": f"Excessive wear on {component} exceeded service life threshold",
            "HDF": f"Insufficient heat dissipation caused thermal damage to {component}",
            "PWF": f"Power fluctuation outside operating range damaged {component}",
            "OSF": f"Overstrain condition from excessive load on {component}",
            "RNF": f"Random failure of {component} — no predictable pattern identified",
        }
        return causes.get(failure_mode, f"Unknown failure of {component}")

    def _random_parts(self, machine_type: str) -> list[str]:
        """Return a random subset of consumable parts replaced during a PM event."""
        consumables = {
            "HYP": ["hydraulic filter", "O-ring set", "hydraulic fluid 20L"],
            "SRV": ["brake pad", "lubricant cartridge", "belt"],
            "RBT": ["cable harness", "grease cartridge", "nozzle tip"],
            "OVN": ["air filter", "thermocouple", "gasket set"],
            "PMP": ["seal kit", "bearing set", "coupling spider"],
            "TST": ["calibration weight", "sensor probe"],
            "CNC": ["coolant filter", "way lube", "chip conveyor belt"],
            "CNV": ["roller bearing", "lubrication fitting"],
        }
        parts = consumables.get(machine_type, ["general consumable"])
        n = self.rng.integers(1, min(3, len(parts)) + 1)
        return list(self.rng.choice(parts, size=n, replace=False))

    def _calculate_reliability_metrics(
        self, failures: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Calculate monthly MTBF, MTTR, availability per machine."""
        from collections import defaultdict

        metrics: list[dict[str, Any]] = []
        machine_failures: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for f in failures:
            machine_failures[f["machine_id"]].append(f)

        for machine_id in FACTORY_MACHINES:
            mf = machine_failures.get(machine_id, [])
            for month in range(1, 7):  # 6 months
                month_start = datetime(2026, month, 1)
                if month < 6:
                    month_end = datetime(2026, month + 1, 1)
                else:
                    month_end = datetime(2026, 7, 1)

                operating_hours = (month_end - month_start).total_seconds() / 3600
                month_failures = [
                    f for f in mf
                    if month_start <= f["failure_start"] < month_end
                ]
                n_failures = len(month_failures)
                total_downtime_hrs = sum(f["downtime_min"] for f in month_failures) / 60

                mtbf = operating_hours / max(n_failures, 1)
                mttr = total_downtime_hrs / max(n_failures, 1)
                availability = (operating_hours - total_downtime_hrs) / operating_hours * 100

                metrics.append({
                    "machine_id": machine_id,
                    "period": "monthly",
                    "period_start": month_start.date(),
                    "mtbf_hrs": round(mtbf, 1),
                    "mttr_hrs": round(mttr, 2),
                    "mttf_hrs": round(mtbf * 0.9, 1),
                    "availability_pct": round(availability, 2),
                    "failure_rate": round(1 / mtbf, 6) if mtbf > 0 else 0,
                    "total_downtime_hrs": round(total_downtime_hrs, 2),
                    "planned_downtime_hrs": round(total_downtime_hrs * 0.3, 2),
                    "unplanned_downtime_hrs": round(total_downtime_hrs * 0.7, 2),
                    "num_failures": n_failures,
                    "num_repairs": n_failures + int(self.rng.integers(0, 3)),
                    "total_repair_cost": round(
                        sum(f.get("cost_parts", 0) + f.get("cost_labor", 0) for f in month_failures),
                        2,
                    ),
                    "reliability_score": round(min(100.0, availability * (mtbf / 500)), 1),
                })

        return metrics
