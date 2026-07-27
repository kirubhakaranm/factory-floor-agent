"""Quality generator — dimensional, visual, sampling inspections + rework/scrap."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.config.constants import AQL_LEVELS, STATION_DEFECTS, generate_inspection_id
from src.datagen.factory_model import ALL_STATION_IDS, FACTORY_STATIONS
from src.datagen.generators.base import BaseGenerator


class QualityGenerator(BaseGenerator):
    """Generates dimensional_inspections, sampling_inspections, visual_checklists,
    rework_records, scrap_records for Postgres. Also spc_measurements and
    process_capability_history for ClickHouse.
    """

    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None) -> None:
        """Initialize quality generator with per-record sequence counters."""
        super().__init__(days, seed, start_date)
        self._dim_seq = 0
        self._smp_seq = 0
        self._vis_seq = 0
        self._rwk_seq = 0
        self._scrap_seq = 0

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate all quality tables: dimensional, sampling, visual, rework, scrap, SPC, capability."""
        dimensional: list[dict[str, Any]] = []
        sampling: list[dict[str, Any]] = []
        visual: list[dict[str, Any]] = []
        rework: list[dict[str, Any]] = []
        scrap: list[dict[str, Any]] = []
        spc: list[dict[str, Any]] = []
        capability: list[dict[str, Any]] = []

        # Dimensional measurements per station per day
        for day in range(self.days):
            date = self.start_date + timedelta(days=day)
            if not self.production_active(date):
                continue

            for station_id in ALL_STATION_IDS:
                station = FACTORY_STATIONS[station_id]
                measurements_per_day = int(self.rng.integers(50, 90))

                for _ in range(measurements_per_day):
                    d, rw, sc = self._generate_dimensional(station_id, station.target_fpy, date)
                    dimensional.append(d)
                    if rw:
                        rework.append(rw)
                    if sc:
                        scrap.append(sc)

        # Sampling inspections (AQL-based, ~30 per day)
        for day in range(self.days):
            date = self.start_date + timedelta(days=day)
            if not self.production_active(date):
                continue
            for _ in range(int(self.rng.integers(25, 35))):
                station_id = self.rng.choice(ALL_STATION_IDS)
                sampling.append(self._generate_sampling(station_id, date))

        # Visual checklists (3 gates: after welding, after paint, after final fit)
        visual_gates = ["WLD-03-RCL", "PNT-03-CLR", "ASM-03-FNL"]
        units_per_day = 80
        for day in range(self.days):
            date = self.start_date + timedelta(days=day)
            if not self.production_active(date):
                continue
            actual_units = int(units_per_day * (0.3 if self.is_weekend(date) else 1.0))
            for gate in visual_gates:
                for u in range(actual_units):
                    visual.append(self._generate_visual_checklist(gate, date, u))

        # SPC measurements (per station per parameter, 60 per day)
        spc_params = {
            "STP-01-PRS": ["panel_thickness", "draw_depth", "surface_roughness",
                           "blank_position", "press_force", "cushion_pressure"],
            "WLD-01-UBD": ["nugget_diameter", "weld_current", "squeeze_time",
                           "electrode_force", "weld_time", "shunt_distance"],
            "PNT-02-PRM": ["film_thickness", "gloss_level", "color_delta_e",
                           "viscosity", "flow_rate", "booth_humidity"],
            "ASM-01-PWR": ["torque_value", "bolt_angle", "gap_measurement",
                           "fluid_level", "connector_force", "alignment_offset"],
        }
        for station_id, params in spc_params.items():
            for param in params:
                daily_spc = self._generate_spc_series(station_id, param)
                spc.extend(daily_spc)

        # Process capability (daily Cpk per station per param)
        for station_id, params in spc_params.items():
            for param in params:
                for day in range(self.days):
                    date = self.start_date + timedelta(days=day)
                    capability.append(self._generate_capability(station_id, param, date))

        return {
            "dimensional_inspections": dimensional,
            "sampling_inspections": sampling,
            "visual_checklists": visual,
            "rework_records": rework,
            "scrap_records": scrap,
            "spc_measurements": spc,
            "process_capability_history": capability,
        }

    def _generate_dimensional(
        self, station_id: str, target_fpy: float, date: datetime
    ) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
        """Generate one dimensional inspection row and an optional rework or scrap row."""
        self._dim_seq += 1
        nominal = float(self.rng.uniform(5.0, 50.0))
        tolerance = nominal * 0.02
        actual = nominal + self.rng.normal(0, tolerance / 3)
        passed = abs(actual - nominal) <= tolerance

        # Force some failures based on FPY target
        if self.rng.random() > target_fpy:
            actual = nominal + self.rng.choice([-1, 1]) * tolerance * self.rng.uniform(1.1, 2.0)
            passed = False

        row = {
            "insp_id": generate_inspection_id("DIM", self._dim_seq),
            "vin_id": None,  # linked during correlation
            "station_id": station_id,
            "measurement_name": f"dim_{self._dim_seq % 20 + 1}",
            "nominal": round(nominal, 3),
            "upper_tol": round(nominal + tolerance, 3),
            "lower_tol": round(nominal - tolerance, 3),
            "actual_value": round(float(actual), 3),
            "result": "pass" if passed else "fail",
            "timestamp": date + timedelta(minutes=int(self.rng.integers(0, 1440))),
        }

        rework_row = None
        scrap_row = None
        if not passed:
            event_time = date + timedelta(minutes=int(self.rng.integers(0, 1440)))
            if self.rng.random() < 0.85:  # 85% rework, 15% scrap
                self._rwk_seq += 1
                defects = STATION_DEFECTS.get(station_id, ["unknown"])
                rework_row = {
                    "rework_id": f"RWK-{self._rwk_seq:06d}",
                    "vin_id": None,
                    "station_id": station_id,
                    "defect_type": self.rng.choice(defects),
                    "rework_action": "adjust and re-measure",
                    "rework_time_min": int(self.rng.integers(5, 45)),
                    "re_inspect_result": "pass" if self.rng.random() < 0.9 else "fail",
                    "cost": round(float(self.rng.uniform(20, 200)), 2),
                    "timestamp": event_time,
                }
            else:
                self._scrap_seq += 1
                scrap_row = {
                    "scrap_id": f"SCRAP-{self._scrap_seq:06d}",
                    "vin_id": None,
                    "station_id": station_id,
                    "reason": self.rng.choice(STATION_DEFECTS.get(station_id, ["unknown"])),
                    "cost": round(float(self.rng.uniform(50, 2000)), 2),
                    "timestamp": event_time,
                }

        return row, rework_row, scrap_row

    def _generate_sampling(self, station_id: str, date: datetime) -> dict[str, Any]:
        """Generate one AQL sampling inspection row for a station and date."""
        self._smp_seq += 1
        aql_type = self.rng.choice(["normal", "tightened", "reduced"])
        aql = AQL_LEVELS[aql_type]
        lot_size = int(self.rng.integers(50, 200))
        sample_size = max(5, int(lot_size * aql["sample_ratio"]))
        accept_number = max(0, int(sample_size * aql["aql"] / 100))
        defects_found = int(self.rng.poisson(accept_number * 0.6))
        disposition = "accept" if defects_found <= accept_number else "reject"

        # Lot number ties this sampling event to a specific incoming material lot
        stage = station_id[:3]
        lot_number = f"LOT-{stage}-{date.strftime('%y%m')}-{self._smp_seq:04d}"

        return {
            "insp_id": generate_inspection_id("SMP", self._smp_seq),
            "station_id": station_id,
            "lot_number": lot_number,
            "lot_size": lot_size,
            "sample_size": sample_size,
            "aql_level": aql["aql"],
            "accept_number": accept_number,
            "reject_number": accept_number + 1,
            "defects_found": defects_found,
            "disposition": disposition,
            "inspection_type": self.rng.choice(["visual", "functional", "destructive"]),
            "timestamp": date + timedelta(minutes=int(self.rng.integers(0, 1440))),
        }

    def _generate_visual_checklist(
        self, station_id: str, date: datetime, unit_idx: int
    ) -> dict[str, Any]:
        """Generate one visual checklist row for a unit passing through a gate station."""
        self._vis_seq += 1
        checkpoints = STATION_DEFECTS.get(station_id, ["general"])
        results = {}
        for cp in checkpoints:
            results[cp] = "OK" if self.rng.random() < 0.96 else "NG"

        return {
            "checklist_id": f"VIS-{self._vis_seq:06d}",
            "vin_id": None,
            "station_id": station_id,
            "checkpoint_items": results,
            "defect_category": (
                "cosmetic" if self.rng.random() < 0.6 else
                "functional" if self.rng.random() < 0.8 else "safety"
            ),
            "timestamp": date + timedelta(minutes=int(self.rng.integers(0, 1440))),
        }

    def _generate_spc_series(self, station_id: str, parameter: str) -> list[dict[str, Any]]:
        """Generate SPC measurements for one station/parameter across all days."""
        rows = []
        target = float(self.rng.uniform(10.0, 100.0))
        spec_range = target * 0.05
        usl = target + spec_range
        lsl = target - spec_range
        process_std = spec_range / 4  # Cpk ~1.33

        for day in range(self.days):
            date = self.start_date + timedelta(days=day)
            n_readings = int(self.rng.integers(50, 70))

            for i in range(n_readings):
                value = self.rng.normal(target, process_std)
                ts = date + timedelta(minutes=int(i * (1440 / n_readings)))

                # Calculate control limits from recent readings
                ucl = target + 3 * process_std
                lcl = target - 3 * process_std

                rows.append({
                    "timestamp": ts,
                    "station_id": station_id,
                    "parameter": parameter,
                    "value": round(float(value), 4),
                    "ucl": round(ucl, 4),
                    "lcl": round(lcl, 4),
                    "usl": round(usl, 4),
                    "lsl": round(lsl, 4),
                    "target": round(target, 4),
                    "cp": round(float((usl - lsl) / (6 * process_std)), 3),
                    "cpk": round(float(min(
                        (usl - target) / (3 * process_std),
                        (target - lsl) / (3 * process_std),
                    )), 3),
                })

        return rows

    def _generate_capability(
        self, station_id: str, parameter: str, date: datetime
    ) -> dict[str, Any]:
        """Generate one daily process capability row (Cp, Cpk) for a station parameter."""
        base_cpk = float(self.rng.uniform(1.1, 1.8))
        # Add some drift over time
        day_idx = (date - self.start_date).days
        drift = -0.001 * day_idx * self.rng.uniform(0, 1)
        cpk = max(0.5, base_cpk + drift + self.rng.normal(0, 0.05))
        cp = cpk + abs(self.rng.normal(0, 0.1))

        return {
            "timestamp": date.date(),
            "station_id": station_id,
            "parameter": parameter,
            "cp": round(float(cp), 3),
            "cpk": round(float(cpk), 3),
            "pp": round(float(cp * self.rng.uniform(0.95, 1.0)), 3),
            "ppk": round(float(cpk * self.rng.uniform(0.93, 1.0)), 3),
            "out_of_control_signals": int(self.rng.poisson(0.5)),
            "trending_alert": 1 if cpk < 1.0 else 0,
        }
