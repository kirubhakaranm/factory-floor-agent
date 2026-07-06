"""FastAPI application factory for PrimeEV Factory Floor Agent."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.monitoring.logging import setup_logging, get_logger

logger = get_logger("primeev.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("PrimeEV Factory Floor Agent starting", version="0.1.0")
    yield
    logger.info("PrimeEV Factory Floor Agent shutting down")


def create_app() -> FastAPI:
    application = FastAPI(
        title="PrimeEV Factory Floor Agent",
        description="AI agents for manufacturing engineers — diagnose, decide, and act",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from src.api.routes.chat import router as chat_router
    from src.api.routes.factory import router as factory_router
    from src.api.routes.alerts import router as alerts_router
    from src.api.routes.sessions import router as sessions_router
    from src.api.routes.health import router as health_router
    from src.monitoring.metrics import router as metrics_router

    application.include_router(chat_router)
    application.include_router(factory_router)
    application.include_router(alerts_router)
    application.include_router(sessions_router)
    application.include_router(health_router)
    application.include_router(metrics_router)

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )

    return application


app = create_app()
