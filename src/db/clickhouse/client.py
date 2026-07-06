"""ClickHouse client wrapper."""

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from src.config.settings import settings

_client: Client | None = None


def get_clickhouse_client() -> Client:
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
    return _client


def insert_dataframe(table: str, data: list[dict], column_names: list[str]) -> None:
    """Bulk insert rows into ClickHouse."""
    client = get_clickhouse_client()
    rows = [[row.get(col) for col in column_names] for row in data]
    client.insert(table, rows, column_names=column_names)


def query(sql: str) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    client = get_clickhouse_client()
    result = client.query(sql)
    columns = result.column_names
    return [dict(zip(columns, row)) for row in result.result_rows]
