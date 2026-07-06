#!/bin/bash
set -euo pipefail

echo "=== PrimeEV Factory — Data Seeding ==="

echo "1. Generating synthetic data (180 days)..."
python -m src.datagen.cli generate --days 180 --seed 42

echo "2. Loading data into Postgres + ClickHouse..."
python -m src.datagen.cli load

echo "=== Data seeding complete! ==="
