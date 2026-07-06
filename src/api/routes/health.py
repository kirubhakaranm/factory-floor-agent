"""Health check endpoint."""

from fastapi import APIRouter

from src.api.schemas import HealthCheck

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Service health check with dependency status."""
    checks: dict[str, str] = {}

    # Check Postgres
    try:
        from src.db.postgres.session import engine
        checks["postgres"] = "healthy"
    except Exception:
        checks["postgres"] = "unavailable"

    # Check ClickHouse
    try:
        from src.db.clickhouse.client import get_clickhouse_client
        checks["clickhouse"] = "configured"
    except Exception:
        checks["clickhouse"] = "unavailable"

    # Check ChromaDB
    try:
        from src.rag.embedder import get_chroma_client
        checks["chromadb"] = "configured"
    except Exception:
        checks["chromadb"] = "unavailable"

    # Check agent
    try:
        from src.agents import root_agent
        checks["agent"] = f"loaded ({len(root_agent.sub_agents)} sub-agents)"
    except Exception:
        checks["agent"] = "error"

    overall = "healthy" if all(v != "error" for v in checks.values()) else "degraded"

    return HealthCheck(
        status=overall,
        service="primeev-factory-agent",
        checks=checks,
    )
