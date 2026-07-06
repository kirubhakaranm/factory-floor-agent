"""CLI for PrimeEV synthetic data generation."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from src.datagen.generators.degradation import DegradationGenerator
from src.datagen.generators.energy import EnergyGenerator
from src.datagen.generators.failures import FailureGenerator
from src.datagen.generators.inventory import InventoryGenerator
from src.datagen.generators.metadata import MetadataGenerator
from src.datagen.generators.production import ProductionGenerator
from src.datagen.generators.quality import QualityGenerator
from src.datagen.generators.supply_chain import SupplyChainGenerator
from src.datagen.generators.telemetry import TelemetryGenerator


def generate(days: int, seed: int, output_dir: str) -> None:
    """Run all generators and write output to JSON files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    generators = [
        ("metadata", MetadataGenerator(days=days, seed=seed)),
        ("production", ProductionGenerator(days=days, seed=seed)),
        ("supply_chain", SupplyChainGenerator(days=days, seed=seed)),
        ("inventory", InventoryGenerator(days=days, seed=seed)),
        ("failures", FailureGenerator(days=days, seed=seed)),
        ("quality", QualityGenerator(days=days, seed=seed)),
        ("energy", EnergyGenerator(days=days, seed=seed)),
        ("telemetry", TelemetryGenerator(days=days, seed=seed, interval_seconds=60)),
        ("degradation", DegradationGenerator(days=days, seed=seed)),
    ]

    all_data: dict[str, list[dict[str, Any]]] = {}
    total_rows = 0

    for name, gen in generators:
        print(f"  Generating {name}...", end=" ", flush=True)
        t0 = time.time()
        data = gen.generate()
        elapsed = time.time() - t0

        for table_name, rows in data.items():
            if table_name not in all_data:
                all_data[table_name] = []
            all_data[table_name].extend(rows)
            total_rows += len(rows)

        row_count = sum(len(v) for v in data.values())
        print(f"{row_count:,} rows ({elapsed:.1f}s)")

    # Write each table to a separate JSON file
    print(f"\n  Writing {len(all_data)} tables to {output}/...")
    for table_name, rows in all_data.items():
        file_path = output / f"{table_name}.json"
        with open(file_path, "w") as f:
            json.dump(rows, f, default=str, indent=None)
        print(f"    {table_name}: {len(rows):,} rows -> {file_path.name}")

    print(f"\n  Total: {total_rows:,} rows across {len(all_data)} tables")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PrimeEV Motors — Synthetic Factory Data Generator"
    )
    subparsers = parser.add_subparsers(dest="command")

    gen_parser = subparsers.add_parser("generate", help="Generate synthetic data")
    gen_parser.add_argument("--days", type=int, default=180, help="Days of history (default: 180)")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    gen_parser.add_argument("--output", type=str, default="data", help="Output directory")

    load_parser = subparsers.add_parser("load", help="Load data into databases")
    load_parser.add_argument("--input", type=str, default="data", help="Input directory")

    args = parser.parse_args()

    if args.command == "generate":
        print(f"=== PrimeEV Factory Data Generator ===")
        print(f"  Days: {args.days} | Seed: {args.seed} | Output: {args.output}/\n")
        generate(args.days, args.seed, args.output)
        print("\n=== Generation complete! ===")

    elif args.command == "load":
        from pathlib import Path
        from src.datagen.loader import load_clickhouse, load_postgres

        data_dir = Path(args.input)
        print(f"=== PrimeEV Factory Data Loader ===")
        print(f"  Input: {data_dir}/\n")

        print("  Loading Postgres...")
        load_postgres(data_dir)

        print("\n  Loading ClickHouse...")
        load_clickhouse(data_dir)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
