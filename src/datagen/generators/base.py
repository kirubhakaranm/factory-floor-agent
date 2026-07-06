"""Base generator with shared timestamp, entity, and shift logic."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.config.constants import SHIFTS, ShiftConfig


class BaseGenerator(ABC):
    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None):
        self.days = days
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.start_date = start_date or datetime(2026, 1, 1, 0, 0, 0)
        self.end_date = self.start_date + timedelta(days=days)

    @abstractmethod
    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate data and return as dict of table_name -> list of row dicts."""
        ...

    def get_shift(self, dt: datetime) -> ShiftConfig:
        hour = dt.hour
        if 6 <= hour < 14:
            return SHIFTS["day"]
        elif 14 <= hour < 22:
            return SHIFTS["swing"]
        else:
            return SHIFTS["night"]

    def get_shift_name(self, dt: datetime) -> str:
        return self.get_shift(dt).name

    def iter_timestamps(
        self, interval_seconds: int = 60, jitter_seconds: int = 0
    ) -> list[datetime]:
        """Generate timestamps from start to end at given interval."""
        timestamps = []
        current = self.start_date
        while current < self.end_date:
            if jitter_seconds > 0:
                jitter = self.rng.integers(-jitter_seconds, jitter_seconds + 1)
                ts = current + timedelta(seconds=int(jitter))
            else:
                ts = current
            timestamps.append(ts)
            current += timedelta(seconds=interval_seconds)
        return timestamps

    def iter_daily_timestamps(self) -> list[datetime]:
        """Generate one timestamp per day at midnight."""
        return [self.start_date + timedelta(days=d) for d in range(self.days)]

    def iter_shift_timestamps(self) -> list[tuple[datetime, str]]:
        """Generate one entry per shift per day."""
        result = []
        for day in range(self.days):
            base = self.start_date + timedelta(days=day)
            for shift_key, shift in SHIFTS.items():
                ts = base.replace(hour=shift.start_hour % 24, minute=0, second=0)
                result.append((ts, shift.name))
        return result

    def is_weekend(self, dt: datetime) -> bool:
        return dt.weekday() >= 5

    def production_active(self, dt: datetime) -> bool:
        """Production runs 24/5, reduced on weekends."""
        return not self.is_weekend(dt) or self.rng.random() < 0.3
