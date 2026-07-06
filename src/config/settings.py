"""Application settings loaded from environment variables."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    # Postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "primeev_factory"
    postgres_user: str = "primeev"
    postgres_password: str = "primeev_dev"

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_db: str = "primeev_telemetry"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"

    # Monitoring
    prometheus_port: int = 9090
    grafana_port: int = 3001

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()

# Export to OS env so litellm and google-adk can pick them up
if settings.gemini_api_key:
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)
if settings.anthropic_api_key:
    os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
