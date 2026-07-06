# PrimeEV Motors — Factory Floor AI Agent

Production-grade multi-agent AI system that helps manufacturing engineers **diagnose, decide, and act** on an EV assembly factory floor.

Built with **Google ADK** + **Claude** (Anthropic) + **Postgres** + **ClickHouse** + **Kafka** + **React**.

## Architecture

```
                         User Query
                             │
                             ▼
                    ┌─────────────────┐
                    │   Root Agent    │  Google ADK + Claude (LiteLLM)
                    │   (Router)      │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────────────┐
            ▼                ▼                ▼        ▼              ▼
    ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌─────────┐
    │  Equipment   │ │  Quality   │ │ Production │ │ Improve- │ │ Action  │
    │  Agent       │ │  Agent     │ │ Agent      │ │ ment     │ │ Agent   │
    │  (19 tools)  │ │  (16 tools)│ │ (16 tools) │ │ (13)     │ │ (8)     │
    └──────┬───────┘ └─────┬──────┘ └─────┬──────┘ └────┬─────┘ └────┬────┘
           │               │              │              │            │
           └───────────────┼──────────────┼──────────────┘            │
                           ▼              ▼                           ▼
              ┌─────────────────────────────────────┐    ┌──────────────────┐
              │         Agent Tools (~48)            │    │  Action Tools    │
              └──────┬──────────┬──────────┬────────┘    │  (work orders,   │
                     │          │          │             │   8D, NCR, PDCA) │
                     ▼          ▼          ▼             └──────────────────┘
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Postgres │ │ClickHouse│ │ ChromaDB │
              │ (31 tbl) │ │ (7 tbl)  │ │ (RAG)    │
              └──────────┘ └──────────┘ └──────────┘
                               ▲
                               │
                    ┌──────────┴──────────┐
                    │   Kafka Streaming   │
                    │   (live sensors)    │
                    └─────────────────────┘
```

## Factory Domain

**PrimeEV Motors** — fictional EV manufacturer with a 5-stage assembly line:

| Stage | Stations | Key Operations |
|-------|----------|----------------|
| Stamping (STP) | Press 1, Press 2, Trim/Pierce | Body panel forming, trimming, piercing |
| Welding (WLD) | Underbody, Side Panel, Roof | Spot welding, body-in-white assembly |
| Paint (PNT) | E-Coat, Prime/Base, Clear/Cure | Corrosion protection, color, clear coat |
| Assembly (ASM) | Powertrain, Interior, Final Fit | Battery, motor, interior, closures |
| Quality (QAT) | Alignment, Water Leak, Dyno | Final inspection and testing |

**3 Vehicle Models:** PE-SD100 (Sedan), PE-SV200 (SUV), PE-CP300 (Compact)  
**~30 machines** with realistic sensor data, failure modes, and degradation curves  
**5 suppliers** with receiving inspections, scorecards, and NCR tracking

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Anthropic API key

### Setup

```bash
# Clone and enter project
cd factory-floor-agent

# Copy environment file and add your API key
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY=sk-ant-xxxxx

# Install dependencies
pip install -e ".[dev]"
cd frontend && npm install && cd ..

# Start infrastructure
docker compose up -d postgres clickhouse chroma zookeeper kafka prometheus grafana

# Generate and load synthetic data
python -m src.datagen.cli generate --days 180 --seed 42
python -m src.datagen.cli load

# Index RAG documents
python -c "from src.rag.embedder import index_all_documents; index_all_documents()"

# Start API server
uvicorn src.api.main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend && npm run dev
```

Open http://localhost:3000 to access the dashboard.

### Run Tests

```bash
# All tests (backend + eval framework)
pytest tests/ evals/ -v

# Just backend
pytest tests/ -v

# Just eval framework
pytest evals/ -v
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | Google ADK 2.x | Multi-agent orchestration, tool routing |
| LLM | Claude Sonnet (via LiteLLM) | Reasoning, diagnosis, recommendations |
| Backend | FastAPI + SSE | API server with streaming chat |
| Frontend | React + TypeScript + Tailwind | Dashboard, chat UI, analytics |
| Operational DB | PostgreSQL 16 | Failures, work orders, inspections, BOMs (~31 tables) |
| Analytics DB | ClickHouse 24.x | Sensor telemetry, OEE, SPC, reliability (~7 tables, ~25M rows) |
| Vector Store | ChromaDB | RAG over SOPs, manuals, FMEAs, troubleshooting DB |
| Streaming | Apache Kafka | Live sensor feeds, real-time alerts |
| Monitoring | Prometheus + Grafana | Agent latency, tool calls, error rates |
| CI/CD | GitHub Actions | Lint, type-check, test, eval on every PR |

## Agent Capabilities

### Equipment Agent
- Multi-step root cause analysis for failures
- Sensor trend analysis and anomaly detection
- Predictive maintenance with RUL estimation
- MTBF/MTTR reliability reporting
- Spare parts availability checks

### Quality Agent
- SPC monitoring with Western Electric rules
- Process capability (Cpk) assessment and trending
- AQL sampling lot accept/reject decisions
- Supplier quality analysis (scorecards, NCRs)
- Rework/scrap tracking and COPQ analysis

### Production Agent
- OEE breakdown (Availability x Performance x Quality)
- VIN traceability (station-by-station production history)
- BOM/MRP queries for production planning
- Shift/period/station comparisons
- Inventory monitoring with reorder alerts

### Improvement Agent (PDCA)
- Before/after analysis with quantified metrics
- PDCA cycle documentation
- FMEA risk assessment references
- Process change effectiveness validation

### Action Agent
- Work order generation
- 8D problem-solving reports
- Supplier NCR issuance
- PDCA record creation
- Maintenance scheduling

## Data Model

### Synthetic Data Generator
Generates realistic, correlated factory data borrowing statistical distributions from:
- **AI4I 2020** — sensor distributions, 5 failure mode logic
- **C-MAPSS** — degradation curves, RUL patterns
- **SECOM** — quality inspection pass/fail distributions
- **Steel Energy** — energy consumption temporal patterns

All data shares consistent entity IDs (VINs, machine IDs, batch IDs) and causal correlations.

### RAG Corpus (177 chunks from 24 documents)
- 15 Standard Operating Procedures (one per station)
- 5 Equipment Manuals (per machine type)
- 3 Troubleshooting Records (root cause investigations)
- 1 Process FMEA with RPN scores
- 1 Case Study (5-Why analysis)
- Process specifications with SPC requirements

## Evaluation System

**36 eval cases** across 5 categories with **5 custom graders**:
- **Correctness** — key facts from ground truth present in response
- **Citation Quality** — data sources cited with entity IDs and numeric values
- **Confidence Calibration** — stated confidence matches evidence (overconfidence penalized harshly)
- **Hallucination Detection** — claims verified against tool call outputs
- **Action Validity** — recommendations are specific, prioritized, and entity-referenced

CI runs eval framework on every PR. Threshold gates block merge if scores drop.

## Project Structure

```
factory-floor-agent/
├── src/
│   ├── config/          # Settings, factory constants, naming conventions
│   ├── datagen/         # Synthetic data generator (9 generators, 30 tables)
│   ├── db/              # Postgres (SQLAlchemy) + ClickHouse + ChromaDB clients
│   ├── streaming/       # Kafka producer, consumer, factory simulator
│   ├── rag/             # Document corpus + chunker + embedder
│   ├── agents/          # Google ADK agents, prompts, tools, callbacks
│   ├── api/             # FastAPI routes (chat SSE, factory, alerts, health)
│   └── monitoring/      # Structured logging, Prometheus metrics, tracing
├── frontend/            # React + TypeScript + Tailwind (5 pages)
├── evals/               # 36 eval cases + 5 graders + runner + CI reporter
├── tests/               # Unit + integration tests
├── infra/               # Docker, Kafka, ClickHouse, Prometheus, Grafana configs
└── scripts/             # Setup, seed, RAG indexing scripts
```

## License

MIT
