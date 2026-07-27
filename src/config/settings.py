"""Application settings loaded from environment variables."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment variables or a .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    # Agent model — set to "ollama/qwen2.5:14b" (or any LiteLLM model string) to
    # run agents locally via Ollama instead of the Anthropic API.
    # Ollama base URL is only needed when agent_model starts with "ollama/".
    agent_model: str = "anthropic/claude-haiku-4-5"
    ollama_base_url: str = "http://localhost:11434"

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
        """Async SQLAlchemy connection URL using asyncpg driver."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_url_sync(self) -> str:
        """Synchronous psycopg2 connection URL for blocking query helpers."""
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
