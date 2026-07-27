#!/bin/bash
set -euo pipefail

echo "=== PrimeEV Factory Floor Agent — Setup ==="

# 1. Env file
echo ""
echo "1. Environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   .env created from template."
    echo "   ACTION REQUIRED: set ANTHROPIC_API_KEY in .env before starting agents."
else
    echo "   .env already exists — skipping."
fi

# 2. Python deps
echo ""
echo "2. Python dependencies..."
pip install -e ".[dev]" --quiet

# 3. Frontend deps
echo ""
echo "3. Frontend dependencies..."
cd frontend && npm install --silent && cd ..

# 4. Infrastructure
echo ""
echo "4. Starting infrastructure (Postgres, ClickHouse, Chroma, Kafka, Prometheus, Grafana)..."
docker compose up -d postgres clickhouse chroma zookeeper kafka prometheus grafana

# 5. Wait for DB health checks
echo ""
echo "5. Waiting for databases to be ready..."
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U primeev -d primeev_factory -q 2>/dev/null; then
        echo "   Postgres ready."
        break
    fi
    sleep 2
done

for i in {1..30}; do
    if docker compose exec -T clickhouse clickhouse-client --query "SELECT 1" -q 2>/dev/null; then
        echo "   ClickHouse ready."
        break
    fi
    sleep 2
done

echo ""
echo "=== Infrastructure ready. ==="
echo ""
echo "Next steps (run once on a fresh install):"
echo ""
echo "  # Generate + load 180 days of synthetic factory data"
echo "  python -m src.datagen generate --days 180 --seed 42"
echo ""
echo "  # Index RAG corpus into ChromaDB"
echo "  python -m src.rag.embedder --index-all"
echo ""
echo "Then start the app:"
echo ""
echo "  # Option A — Docker (recommended, seeds automatically)"
echo "  docker compose up"
echo ""
echo "  # Option B — Dev mode (hot-reload)"
echo "  uvicorn src.api.main:app --reload --port 8000"
echo "  cd frontend && npm run dev"
echo ""
echo "Services:"
echo "  Dashboard  http://localhost:3000"
echo "  API docs   http://localhost:8000/docs"
echo "  Grafana    http://localhost:3001  (admin / admin)"
echo "  Prometheus http://localhost:9090"
echo ""
echo "Run evals:"
echo "  pytest evals/ -v -k 'not test_live_eval'   # offline, ~3s"
echo "  pytest evals/ -v --live                    # live agent (requires running services)"
echo "  pytest evals/ -v --live --llm-judge        # + faithfulness/relevance graders"
