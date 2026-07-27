"""Production tools — batches, OEE, cycle times, throughput."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.clickhouse import queries as ch
from src.db.postgres import queries as pg


def get_batch_status(batch_id: str) -> dict | str:
    """[ACTION]: Retrieve production batch details — units produced, yield, and timing. [TARGET]: production_batches table (Postgres).

    [INPUT PREREQUISITE]: batch_id must be a valid batch identifier in format B-XXXXXX
    (e.g. 'B-000042'). Obtain batch IDs from vin_registry or production context.

    [OUTPUT GUARANTEE]: Returns a single dict with: batch_id, line_id, model_id, start_time,
    end_time, units_produced, units_passed, yield_pct. All timestamps are ISO strings.

    [NEGATIVE BOUNDARY]: Cannot return individual VIN-level pass/fail within the batch.
    Cannot return batch quality inspection details — use get_sampling_results for that.
    Cannot list multiple batches — this is a single-batch lookup by ID.

    Args:
        batch_id: Batch identifier (e.g. 'B-000042')

    Returns:
        Batch record dict, or TERMINAL string if not found.
    """
    record = pg.sync_get_batch_status(batch_id)
    if not record:
        return (
            f"TERMINAL: Batch '{batch_id}' not found in production_batches. "
            "Verify the batch_id format (e.g. B-000042). Do not retry — ask the user to confirm."
        )
    return record


def get_oee_metrics(
    station_id: str,
    shift: Literal["Day", "Swing", "Night"] | None = None,
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of history (1–365)")] = 30,
) -> list[dict] | str:
    """[ACTION]: Retrieve OEE (Overall Equipment Effectiveness) daily breakdown for a station. [TARGET]: oee_metrics table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'ASM-01-PWR').
    shift must be exactly 'Day', 'Swing', or 'Night' if provided — case-sensitive.

    [OUTPUT GUARANTEE]: Returns daily rows with: date, shift, avg_availability, avg_performance,
    avg_quality, avg_oee — all as decimals (0.0–1.0). OEE = Availability × Performance × Quality.
    Rows are ordered by date and shift. Target OEE is ≥0.75 (75%).

    [NEGATIVE BOUNDARY]: Cannot return OEE for a stage (multi-station) — call per station then
    aggregate. Cannot return real-time OEE — data is shift-level aggregated. Empty list means
    no OEE data for the station; do not retry with a different station.

    Args:
        station_id: Station identifier (e.g. 'ASM-01-PWR')
        shift: Filter by shift name (optional): 'Day', 'Swing', or 'Night'
        days_back: Days of history (default 30)

    Returns:
        List of daily OEE rows. Empty list if no data for this station.
    """
    data = ch.get_oee_metrics(station_id, shift, days_back)
    if not data:
        return (
            f"TERMINAL: No OEE data found for station '{station_id}' "
            f"(shift={shift}, days_back={days_back}). "
            "Verify the station_id is correct. Do not retry with different parameters."
        )
    for row in data:
        row["station_id"] = station_id
    return data


def get_cycle_times(
    station_id: str,
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of OEE history to average performance over (1–365)")] = 7,
) -> dict | str:
    """[ACTION]: Retrieve ideal cycle time for a station and estimate actual cycle time from OEE performance. [TARGET]: factory model (static) + oee_metrics (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'ASM-02-INT').
    The ideal cycle time is a static design parameter from the factory model.

    [OUTPUT GUARANTEE]: Returns a dict with: station_id, ideal_cycle_time_sec (from factory spec),
    days_analyzed, avg_oee_performance (decimal), estimated_actual_cycle_time_sec
    (ideal / performance — null if no OEE data). Use ideal_cycle_time_sec to identify bottlenecks
    (longest ideal cycle time = rate-limiting station).

    [NEGATIVE BOUNDARY]: Cannot return per-unit or per-shift cycle time distributions.
    Cannot return cycle times for stations outside the factory topology.
    estimated_actual_cycle_time_sec is derived from OEE performance ratio, not direct measurement.

    Args:
        station_id: Station identifier (e.g. 'ASM-02-INT')
        days_back: Days of OEE history to average performance over (default 7)

    Returns:
        Cycle time dict, or TERMINAL string if station not found.
    """
    from src.datagen.factory_model import FACTORY_STATIONS
    station = FACTORY_STATIONS.get(station_id)
    if not station:
        return (
            f"TERMINAL: Station '{station_id}' not found in factory topology. "
            "Valid format: STP-01-PRS, WLD-02-SDP, ASM-01-PWR, etc. "
            "Do not retry — verify the station_id."
        )

    ideal_sec = station.cycle_time_sec
    oee_data = ch.get_oee_metrics(station_id, days_back=days_back)

    avg_perf = None
    actual_sec = None
    if oee_data:
        perf_values = [r["avg_performance"] for r in oee_data if r.get("avg_performance")]
        if perf_values:
            avg_perf = sum(perf_values) / len(perf_values)
            actual_sec = round(ideal_sec / avg_perf, 1) if avg_perf > 0 else None

    return {
        "station_id": station_id,
        "ideal_cycle_time_sec": ideal_sec,
        "days_analyzed": days_back,
        "avg_oee_performance": round(avg_perf, 4) if avg_perf else None,
        "estimated_actual_cycle_time_sec": actual_sec,
    }


def get_throughput(
    line_id: str | None = None,
    days_back: Annotated[int, Field(ge=1, le=365, description="Days of history anchored to latest record (1–365)")] = 7,
) -> list[dict] | str:
    """[ACTION]: Retrieve daily production throughput — units produced and passed per day per model. [TARGET]: production_batches table (Postgres).

    [INPUT PREREQUISITE]: line_id is optional; if None, returns factory-wide totals.
    days_back is anchored to the latest production record in the database, not wall-clock time.

    [OUTPUT GUARANTEE]: Returns rows grouped by date and model_id, each with:
    date, model_id, units_produced, units_passed, yield_pct. Ordered newest-first.
    Daily target is 80 vehicles total (PE-SD100: ~31, PE-SV200: ~25, PE-CP300: ~24).

    [NEGATIVE BOUNDARY]: Cannot return hourly or shift-level throughput — use get_oee_metrics
    for shift breakdowns. Cannot filter by station — this is line/factory level.
    line_id filtering is not yet implemented; pass None for factory total.

    Args:
        line_id: Filter by production line (optional — currently ignored, returns factory total)
        days_back: Days of history anchored to latest record (default 7)

    Returns:
        List of daily throughput rows. Empty list means no production data in window.
    """
    data = pg.sync_get_throughput(days_back)
    if not data:
        return (
            f"TERMINAL: No production throughput data found for the last {days_back} days. "
            "The database may have no batches in this window. Do not retry — report no data."
        )
    return data
