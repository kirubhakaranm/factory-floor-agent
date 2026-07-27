"""Production generator — batches, VINs, cycle times, OEE, production orders."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.config.constants import DAILY_PRODUCTION_TARGET, STAGES, generate_vin
from src.datagen.factory_model import (
    ALL_MODEL_IDS,
    ALL_STATION_IDS,
    FACTORY_STATIONS,
    FACTORY_VEHICLE_MODELS,
)
from src.datagen.generators.base import BaseGenerator


class ProductionGenerator(BaseGenerator):
    """Generates VINs, production_batches, production_orders, and oee_metrics."""

    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None) -> None:
        """Initialize production generator with per-model VIN and batch sequence counters."""
        super().__init__(days, seed, start_date)
        self._vin_seq: dict[str, int] = {m: 0 for m in ALL_MODEL_IDS}
        self._batch_seq = 0
        self._po_seq = 0

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate vin_registry, production_batches, production_orders, and oee_metrics."""
        vins: list[dict[str, Any]] = []
        batches: list[dict[str, Any]] = []
        orders: list[dict[str, Any]] = []
        oee: list[dict[str, Any]] = []

        for day in range(self.days):
            date = self.start_date + timedelta(days=day)
            if not self.production_active(date):
                continue

            day_vins, day_batches, day_orders = self._generate_day(date)
            vins.extend(day_vins)
            batches.extend(day_batches)
            orders.extend(day_orders)

        # Generate OEE metrics per station per shift
        for ts, shift_name in self.iter_shift_timestamps():
            if not self.production_active(ts):
                continue
            for station_id in ALL_STATION_IDS:
                oee.append(self._generate_oee(station_id, ts, shift_name))

        return {
            "vin_registry": vins,
            "production_batches": batches,
            "production_orders": orders,
            "oee_metrics": oee,
        }

    def _generate_day(
        self, date: datetime
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Generate VINs, batches, and production orders for all models on a single day."""
        vins = []
        batches = []
        orders = []

        # Production mix: SD100=30, SV200=25, CP300=25
        for model_id, model in FACTORY_VEHICLE_MODELS.items():
            # Weekend: 30% capacity
            daily = model.daily_target
            if self.is_weekend(date):
                daily = max(1, int(daily * 0.3))

            # Some daily variation
            daily = int(daily * self.rng.uniform(0.85, 1.1))

            # Create production order
            self._po_seq += 1
            po_id = f"PO-{date.strftime('%y%m')}-{self._po_seq:05d}"
            orders.append({
                "po_id": po_id,
                "model_id": model_id,
                "quantity": daily,
                "priority": "normal",
                "due_date": date,
            })

            # Split into batches (~7 units each, 3 shifts)
            units_per_batch = max(1, daily // 3)
            remaining = daily
            shift_idx = 0

            while remaining > 0:
                batch_size = min(units_per_batch, remaining)
                self._batch_seq += 1
                batch_id = f"B-{self._batch_seq:06d}"
                shift_name = ["Day", "Swing", "Night"][shift_idx % 3]
                shift_start_hour = [6, 14, 22][shift_idx % 3]

                batch_start = date.replace(hour=shift_start_hour, minute=0, second=0)
                batch_duration = timedelta(minutes=int(batch_size * 8))  # ~8 min per unit

                units_passed = int(batch_size * self.rng.uniform(0.92, 1.0))

                batches.append({
                    "batch_id": batch_id,
                    "line_id": "L1",
                    "model_id": model_id,
                    "start_time": batch_start,
                    "end_time": batch_start + batch_duration,
                    "units_produced": batch_size,
                    "units_passed": units_passed,
                })

                # Generate VINs for this batch
                for _ in range(batch_size):
                    self._vin_seq[model_id] += 1
                    model_code = model_id.replace("PE-", "")
                    vin = generate_vin(model_code, date.year, self._vin_seq[model_id])
                    vins.append({
                        "vin_id": vin,
                        "model_id": model_id,
                        "batch_id": batch_id,
                        "production_date": date,
                        "status": "completed",
                    })

                remaining -= batch_size
                shift_idx += 1

        return vins, batches, orders

    def _generate_oee(self, station_id: str, ts: datetime, shift_name: str) -> dict[str, Any]:
        """Generate one OEE metrics row for a station and shift timestamp."""
        station = FACTORY_STATIONS[station_id]

        # Availability: 88-99% (some downtime)
        availability = float(self.rng.uniform(0.88, 0.99))
        # Performance: 85-100% (speed losses)
        performance = float(self.rng.uniform(0.85, 1.0))
        # Quality: based on station FPY target ± noise
        quality = float(station.target_fpy + self.rng.normal(0, 0.01))
        quality = np.clip(quality, 0.85, 1.0)

        # Night shift slightly lower performance
        if shift_name == "Night":
            performance *= 0.97
            quality *= 0.99

        oee = availability * performance * quality

        return {
            "timestamp": ts,
            "station_id": station_id,
            "shift": shift_name,
            "availability": round(availability, 4),
            "performance": round(performance, 4),
            "quality": round(float(quality), 4),
            "oee": round(float(oee), 4),
        }
