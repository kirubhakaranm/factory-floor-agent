"""Supply chain generator — suppliers, receiving inspections, NCRs, scorecards."""

from datetime import datetime, timedelta
from typing import Any

from src.config.constants import SUPPLIERS
from src.datagen.generators.base import BaseGenerator


class SupplyChainGenerator(BaseGenerator):
    """Generates suppliers, raw_materials, receiving_inspections,
    supplier_scorecards, supplier_ncrs for Postgres.
    """

    def __init__(self, days: int = 180, seed: int = 42, start_date: datetime | None = None):
        super().__init__(days, seed, start_date)
        self._ri_seq = 0
        self._ncr_seq = 0

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        suppliers = self._generate_suppliers()
        raw_materials = self._generate_raw_materials()
        receiving = self._generate_receiving_inspections()
        scorecards = self._generate_scorecards()
        ncrs = self._generate_ncrs()

        return {
            "suppliers": suppliers,
            "raw_materials": raw_materials,
            "receiving_inspections": receiving,
            "supplier_scorecards": scorecards,
            "supplier_ncrs": ncrs,
        }

    def _generate_suppliers(self) -> list[dict[str, Any]]:
        return [
            {
                "supplier_id": sid,
                "name": info["name"],
                "category": info["category"],
                "rating": round(float(self.rng.uniform(3.0, 5.0)), 1),
                "lead_time_days": int(self.rng.integers(3, 21)),
            }
            for sid, info in SUPPLIERS.items()
        ]

    def _generate_raw_materials(self) -> list[dict[str, Any]]:
        materials = [
            ("RAW-STL-001", "SUP-MTL01", "Steel sheet 1.2mm CR"),
            ("RAW-STL-002", "SUP-MTL01", "Steel sheet 0.8mm CR"),
            ("RAW-STL-003", "SUP-MTL01", "Steel sheet 1.5mm CR"),
            ("RAW-ALU-001", "SUP-MTL02", "Aluminum sheet 1.5mm 6016-T4"),
            ("RAW-ALU-002", "SUP-MTL02", "Aluminum extrusion 6063-T5"),
            ("RAW-PLY-001", "SUP-PLY01", "ABS resin pellets"),
            ("RAW-PLY-002", "SUP-PLY01", "EPDM rubber strip"),
            ("RAW-PLY-003", "SUP-PLY01", "Polycarbonate sheet 3mm"),
            ("RAW-PLY-004", "SUP-PLY01", "Polyurethane foam block"),
            ("RAW-ELC-001", "SUP-ELC01", "LFP battery cell 3.2V 50Ah"),
            ("RAW-ELC-002", "SUP-ELC01", "Copper wiring harness 12AWG"),
            ("RAW-ELC-003", "SUP-ELC01", "HV connector assembly"),
            ("RAW-CHM-001", "SUP-CHM01", "E-coat solution 200L drum"),
            ("RAW-CHM-002", "SUP-CHM01", "Basecoat paint — Pearl White"),
            ("RAW-CHM-003", "SUP-CHM01", "Basecoat paint — Midnight Black"),
            ("RAW-CHM-004", "SUP-CHM01", "Clearcoat 2K urethane"),
            ("RAW-CHM-005", "SUP-CHM01", "Body seam sealer cartridge"),
            ("RAW-FST-001", "SUP-MTL01", "M10 flange bolt Grade 10.9"),
            ("RAW-FST-002", "SUP-MTL01", "M8 hex bolt Grade 8.8"),
            ("RAW-FST-003", "SUP-MTL01", "Rivet 4.8mm aluminum"),
            ("RAW-SEL-001", "SUP-CHM01", "Windshield adhesive cartridge"),
            ("RAW-SEL-002", "SUP-PLY01", "Door seal weatherstrip 10m"),
            ("RAW-SEL-003", "SUP-PLY01", "Hood insulation pad"),
            ("RAW-BRK-001", "SUP-MTL01", "Brake disc 330mm ventilated"),
            ("RAW-BRK-002", "SUP-MTL01", "Brake pad set ceramic"),
        ]
        return [
            {"material_id": m[0], "supplier_id": m[1], "part_number": m[0], "description": m[2]}
            for m in materials
        ]

    def _generate_receiving_inspections(self) -> list[dict[str, Any]]:
        rows = []
        supplier_ids = list(SUPPLIERS.keys())
        for day in range(self.days):
            date = self.start_date + timedelta(days=day)
            if self.is_weekend(date):
                continue
            n_deliveries = int(self.rng.integers(3, 8))
            for _ in range(n_deliveries):
                self._ri_seq += 1
                supplier = self.rng.choice(supplier_ids)
                # 95% pass, 3% conditional, 2% reject
                roll = self.rng.random()
                if roll < 0.95:
                    result, disposition = "pass", "accept"
                elif roll < 0.98:
                    result, disposition = "conditional", "conditional"
                else:
                    result, disposition = "fail", "reject"

                rows.append({
                    "ri_id": f"RI-{self._ri_seq:06d}",
                    "material_id": f"RAW-STL-00{self.rng.integers(1, 4)}",
                    "supplier_id": supplier,
                    "lot_number": f"{supplier}-LOT-{date.strftime('%y%m')}-{self.rng.integers(1, 999):03d}",
                    "inspection_date": date,
                    "inspector_id": f"OPR-{self.rng.integers(1, 46):03d}",
                    "result": result,
                    "disposition": disposition,
                    "first_article_status": "approved" if self.rng.random() < 0.9 else "pending",
                })
        return rows

    def _generate_scorecards(self) -> list[dict[str, Any]]:
        rows = []
        for supplier_id in SUPPLIERS:
            for month in range(1, 7):
                defect_ppm = float(self.rng.uniform(50, 500))
                on_time = float(self.rng.uniform(0.85, 0.99))
                quality_score = max(0, 100 - defect_ppm / 10)
                delivery_score = on_time * 100

                rows.append({
                    "supplier_id": supplier_id,
                    "month": datetime(2026, month, 1).date(),
                    "defect_ppm": round(defect_ppm, 1),
                    "on_time_pct": round(on_time * 100, 1),
                    "quality_score": round(quality_score, 1),
                    "delivery_score": round(delivery_score, 1),
                    "overall_grade": (
                        "A" if quality_score > 90 and delivery_score > 95 else
                        "B" if quality_score > 80 and delivery_score > 90 else
                        "C" if quality_score > 70 else "D"
                    ),
                })
        return rows

    def _generate_ncrs(self) -> list[dict[str, Any]]:
        rows = []
        supplier_ids = list(SUPPLIERS.keys())
        for week in range(self.days // 7):
            if self.rng.random() < 0.4:
                self._ncr_seq += 1
                date = self.start_date + timedelta(weeks=week)
                supplier = self.rng.choice(supplier_ids)
                rows.append({
                    "ncr_id": f"NCR-{supplier.split('-')[1]}{self.rng.integers(1,3):02d}-{self._ncr_seq:05d}",
                    "supplier_id": supplier,
                    "lot_id": f"{supplier}-LOT-{date.strftime('%y%m')}-{self.rng.integers(1, 999):03d}",
                    "issue": self.rng.choice([
                        "Dimensional out of spec",
                        "Surface finish defect",
                        "Material certification missing",
                        "Contamination detected",
                        "Wrong part shipped",
                        "Quantity short",
                    ]),
                    "disposition": self.rng.choice(["return", "rework", "use-as-is", "scrap"]),
                    "date": date,
                })
        return rows
