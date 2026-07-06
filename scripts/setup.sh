#!/bin/bash
set -euo pipefail

echo "=== PrimeEV Factory Floor Agent — Setup ==="

echo "1. Creating .env from template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   .env created. Update ANTHROPIC_API_KEY before running agents."
else
    echo "   .env already exists, skipping."
fi

echo "2. Installing Python dependencies..."
pip install -e ".[dev]"

echo "3. Installing frontend dependencies..."
cd frontend && npm install && cd ..

echo "4. Starting infrastructure services..."
docker compose up -d postgres clickhouse chroma zookeeper kafka prometheus grafana

echo "5. Waiting for services to be healthy..."
sleep 10

echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  python -m src.datagen.cli generate --days 180 --seed 42   # Generate data"
echo "  python -m src.datagen.cli load                            # Load into DBs"
echo "  python scripts/index_rag.sh                               # Index RAG documents"
echo "  uvicorn src.api.main:app --reload                         # Start API"
echo "  cd frontend && npm run dev                                # Start frontend"
