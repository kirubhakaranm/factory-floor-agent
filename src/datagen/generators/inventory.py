"""Inventory generator — raw materials, WIP, consumables, spare parts, finished goods."""

from datetime import datetime
from typing import Any

from src.datagen.factory_model import ALL_STATION_IDS, FACTORY_MACHINES
from src.datagen.generators.base import BaseGenerator


class InventoryGenerator(BaseGenerator):
    """Generates inventory snapshot tables for Postgres."""

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "raw_material_inventory": self._generate_raw_material_inventory(),
            "consumables_inventory": self._generate_consumables(),
            "spare_parts_inventory": self._generate_spare_parts(),
        }

    def _generate_raw_material_inventory(self) -> list[dict[str, Any]]:
        materials = [
            ("RAW-STL-001", "Steel sheet 1.2mm CR", "kg", 5000, 2000),
            ("RAW-STL-002", "Steel sheet 0.8mm CR", "kg", 3000, 1500),
            ("RAW-STL-003", "Steel sheet 1.5mm CR", "kg", 4000, 1800),
            ("RAW-ALU-001", "Aluminum sheet 1.5mm 6016-T4", "kg", 2500, 1000),
            ("RAW-ALU-002", "Aluminum extrusion 6063-T5", "kg", 1500, 600),
            ("RAW-PLY-001", "ABS resin pellets", "kg", 800, 300),
            ("RAW-PLY-002", "EPDM rubber strip", "m", 2000, 500),
            ("RAW-ELC-001", "LFP battery cell 3.2V 50Ah", "pcs", 12000, 5000),
            ("RAW-ELC-002", "Copper wiring harness 12AWG", "m", 8000, 3000),
            ("RAW-CHM-001", "E-coat solution 200L drum", "drums", 15, 5),
            ("RAW-CHM-002", "Basecoat paint — Pearl White", "L", 2000, 500),
            ("RAW-CHM-003", "Basecoat paint — Midnight Black", "L", 1500, 400),
            ("RAW-CHM-004", "Clearcoat 2K urethane", "L", 1800, 600),
            ("RAW-FST-001", "M10 flange bolt Grade 10.9", "pcs", 50000, 10000),
            ("RAW-FST-002", "M8 hex bolt Grade 8.8", "pcs", 40000, 8000),
        ]
        rows = []
        for mid, desc, unit, max_qty, reorder in materials:
            qty = int(self.rng.integers(int(reorder * 0.5), int(max_qty * 1.2)))
            rows.append({
                "material_id": mid,
                "description": desc,
                "unit": unit,
                "quantity": qty,
                "reorder_point": reorder,
                "reorder_qty": int(max_qty * 0.6),
                "last_counted": self.end_date.date(),
            })
        return rows

    def _generate_consumables(self) -> list[dict[str, Any]]:
        consumable_templates = {
            "STP": [
                ("Stamping lubricant", "L", 200, 50, 40.0),
                ("Die cleaning solvent", "L", 100, 25, 15.0),
                ("Protective gloves (pair)", "pcs", 500, 100, 0.5),
            ],
            "WLD": [
                ("Weld tip cap", "pcs", 1000, 200, 2.5),
                ("Shielding gas CO2/Ar", "cylinders", 20, 5, 85.0),
                ("Anti-spatter spray", "cans", 100, 30, 8.0),
                ("Electrode dresser blade", "pcs", 50, 10, 35.0),
            ],
            "PNT": [
                ("Paint filter 20μm", "pcs", 200, 50, 12.0),
                ("Masking tape 18mm", "rolls", 300, 80, 3.5),
                ("Booth air filter", "pcs", 30, 8, 45.0),
                ("Solvent flush thinner", "L", 400, 100, 6.0),
            ],
            "ASM": [
                ("Torque tool bit T40", "pcs", 100, 20, 15.0),
                ("Adhesive cartridge", "pcs", 200, 50, 22.0),
                ("Cable ties 200mm", "pcs", 5000, 1000, 0.1),
                ("Thread-locking fluid", "bottles", 50, 10, 18.0),
            ],
            "QAT": [
                ("Calibration shim set", "sets", 10, 3, 120.0),
                ("Water leak test dye", "L", 50, 15, 25.0),
                ("Dyno brake fluid", "L", 100, 30, 15.0),
            ],
        }
        rows = []
        item_seq = 0
        for station_id in ALL_STATION_IDS:
            stage = station_id[:3]
            templates = consumable_templates.get(stage, [])
            for desc, unit, max_qty, min_level, cost_per_unit in templates:
                item_seq += 1
                qty = int(self.rng.integers(int(min_level * 0.3), int(max_qty * 1.1)))
                rows.append({
                    "item_id": f"CON-{item_seq:04d}",
                    "station_id": station_id,
                    "description": desc,
                    "unit": unit,
                    "quantity": qty,
                    "min_level": min_level,
                    "usage_rate_per_shift": round(float(self.rng.uniform(1, max(2, max_qty * 0.05))), 1),
                    "cost_per_unit": cost_per_unit,
                })
        return rows

    def _generate_spare_parts(self) -> list[dict[str, Any]]:
        parts_by_type = {
            "HYP": [
                ("SP-HYP-001", "Hydraulic pump assembly", 2800.0, 14),
                ("SP-HYP-002", "Pressure relief valve", 450.0, 7),
                ("SP-HYP-003", "Cylinder seal kit", 180.0, 3),
                ("SP-HYP-004", "Solenoid valve", 320.0, 7),
                ("SP-HYP-005", "Hydraulic filter element", 65.0, 5),
            ],
            "SRV": [
                ("SP-SRV-001", "Servo motor", 3200.0, 21),
                ("SP-SRV-002", "Encoder module", 890.0, 14),
                ("SP-SRV-003", "Ball screw assembly", 1500.0, 21),
                ("SP-SRV-004", "Brake module", 420.0, 7),
            ],
            "RBT": [
                ("SP-RBT-001", "Joint motor assembly", 4500.0, 28),
                ("SP-RBT-002", "Reducer gear unit", 2200.0, 28),
                ("SP-RBT-003", "Cable harness set", 850.0, 14),
                ("SP-RBT-004", "Weld gun nozzle", 120.0, 3),
                ("SP-RBT-005", "Teach pendant", 1800.0, 14),
            ],
            "OVN": [
                ("SP-OVN-001", "Heating element 5kW", 580.0, 7),
                ("SP-OVN-002", "Thermocouple K-type", 45.0, 3),
                ("SP-OVN-003", "Circulation fan motor", 920.0, 14),
            ],
            "PMP": [
                ("SP-PMP-001", "Impeller assembly", 680.0, 14),
                ("SP-PMP-002", "Mechanical seal kit", 250.0, 7),
                ("SP-PMP-003", "Bearing set", 180.0, 5),
            ],
        }
        rows = []
        for machine_id, machine in FACTORY_MACHINES.items():
            parts = parts_by_type.get(machine["type"], []) if isinstance(machine, dict) else parts_by_type.get(machine.machine_type, [])
            for part_num, desc, cost, lead_time in parts:
                qty = int(self.rng.integers(0, 5))
                rows.append({
                    "part_number": part_num,
                    "description": desc,
                    "compatible_machines": [machine_id],
                    "quantity_on_hand": qty,
                    "reorder_point": 1,
                    "lead_time_days": lead_time,
                    "unit_cost": cost,
                    "location_bin": f"BIN-{self.rng.choice(['A','B','C','D'])}-{self.rng.integers(1,30):02d}",
                    "last_used_date": None,
                })
        return rows
