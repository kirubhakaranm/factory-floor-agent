"""Metadata generator — Faker-based operators, technicians, crews."""

from datetime import datetime
from typing import Any

from faker import Faker

from src.config.constants import SHIFTS
from src.datagen.generators.base import BaseGenerator


class MetadataGenerator(BaseGenerator):
    """Generates operators, technicians, crews for Postgres."""

    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None) -> None:
        """Initialize the metadata generator and seed Faker for reproducible names."""
        super().__init__(days, seed, start_date)
        self.fake = Faker()
        Faker.seed(seed)

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        """Generate operators, technicians, crews, and shifts for the simulation window."""
        operators = self._generate_operators()
        technicians = self._generate_technicians()
        crews = self._generate_crews()
        shifts = self._generate_shifts()
        return {
            "operators": operators,
            "technicians": technicians,
            "crews": crews,
            "shifts": shifts,
        }

    def _generate_operators(self) -> list[dict[str, Any]]:
        """Generate 45 operator records with names, shifts, crews, and certifications."""
        operators = []
        certifications_pool = [
            "Forklift", "Crane", "Welding", "Paint", "HV Safety",
            "First Aid", "Lockout/Tagout", "Quality Inspector",
        ]
        for i in range(1, 46):  # 45 operators
            shift_idx = (i - 1) % 3
            shift_name = list(SHIFTS.values())[shift_idx].name
            crew_idx = ((i - 1) // 15) % 2
            crew_names = list(SHIFTS.values())[shift_idx].crews
            crew = crew_names[crew_idx] if crew_idx < len(crew_names) else crew_names[0]

            n_certs = self.rng.integers(1, 4)
            certs = list(self.rng.choice(certifications_pool, size=n_certs, replace=False))

            operators.append({
                "operator_id": f"OPR-{i:03d}",
                "name": self.fake.name(),
                "shift": shift_name,
                "crew_id": crew,
                "certifications": certs,
                "hire_date": self.fake.date_between(
                    start_date=datetime(2020, 1, 1), end_date=datetime(2025, 12, 31)
                ),
            })
        return operators

    def _generate_technicians(self) -> list[dict[str, Any]]:
        """Generate 12 technician records with names, shifts, and specializations."""
        technicians = []
        specializations_pool = [
            "Hydraulics", "Robotics", "Electrical", "PLC/Controls",
            "Mechanical", "Paint Systems", "Conveyor", "Calibration",
        ]
        for i in range(1, 13):  # 12 technicians
            shift_idx = (i - 1) % 3
            shift_name = list(SHIFTS.values())[shift_idx].name
            n_specs = self.rng.integers(2, 5)
            specs = list(self.rng.choice(specializations_pool, size=n_specs, replace=False))

            technicians.append({
                "tech_id": f"TECH-{i:03d}",
                "name": self.fake.name(),
                "shift": shift_name,
                "specializations": specs,
            })
        return technicians

    def _generate_crews(self) -> list[dict[str, Any]]:
        """Generate one crew record per shift crew defined in the SHIFTS constant."""
        crews = []
        for shift_key, shift_config in SHIFTS.items():
            for crew_name in shift_config.crews:
                crews.append({
                    "crew_id": crew_name,
                    "shift_name": shift_config.name,
                    "supervisor_id": f"OPR-{self.rng.integers(1, 46):03d}",
                })
        return crews

    def _generate_shifts(self) -> list[dict[str, Any]]:
        """Generate one shift record per shift per day across the simulation window."""
        shifts = []
        for ts, shift_name in self.iter_shift_timestamps():
            shift_config = [s for s in SHIFTS.values() if s.name == shift_name][0]
            crew = self.rng.choice(shift_config.crews)
            shifts.append({
                "shift_id": f"SH-{ts.strftime('%Y%m%d')}-{shift_name[:1]}",
                "date": ts.date(),
                "shift_name": shift_name,
                "start_time": ts.replace(hour=shift_config.start_hour % 24),
                "end_time": ts.replace(hour=shift_config.end_hour % 24),
                "crew_id": crew,
                "production_target": int(self.rng.integers(24, 30)),
            })
        return shifts
