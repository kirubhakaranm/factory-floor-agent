"""Reliability metrics tools — MTBF, MTTR, availability, failure rate trends."""

from typing import Annotated

from pydantic import Field

from src.db.clickhouse import queries as ch


def get_mtbf_mttr(machine_id: str) -> list[dict] | str:
    """[ACTION]: Retrieve monthly MTBF, MTTR, and availability history for a single machine. [TARGET]: machine_reliability_metrics table (ClickHouse).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier (e.g. 'STP-01-PRS-HYP01').
    Use this when you need detailed monthly time-series for one machine.
    Use get_reliability_report for a station-level summary across all machines.

    [OUTPUT GUARANTEE]: Returns monthly rows with: period_start, mtbf_hrs, mttr_hrs, mttf_hrs,
    availability_pct, failure_rate, total_downtime_hrs, planned_downtime_hrs,
    unplanned_downtime_hrs, num_failures, num_repairs, total_repair_cost, reliability_score.
    Ordered by period_start ascending.

    [NEGATIVE BOUNDARY]: Cannot return daily or weekly granularity — use period='monthly' only.
    Cannot aggregate across multiple machines — use get_reliability_report for station summary.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')

    Returns:
        Monthly reliability metrics list. TERMINAL string if no data found.
    """
    data = ch.get_reliability_metrics(machine_id, period="monthly")
    if not data:
        return (
            f"TERMINAL: No reliability metrics found for machine '{machine_id}'. "
            "Verify the machine_id. Do not retry."
        )
    return data


def get_reliability_report(station_id: str) -> str:
    """[ACTION]: Generate a reliability summary for all machines at a station — MTBF, MTTR, availability. [TARGET]: machine_reliability_metrics (ClickHouse) + factory model.

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'STP-01-PRS').
    Aggregates YTD data across all machines at the station. Use this for 'reliability report'
    or 'MTBF/MTTR comparison' queries about a station.

    [OUTPUT GUARANTEE]: Returns a formatted text report with one line per machine showing:
    machine_id, model, avg MTBF (h), avg MTTR (h), avg Availability (%), total failures YTD,
    and a ⚠ flag for machines with ≥10 failures. Machines with most failures are highlighted.

    [NEGATIVE BOUNDARY]: Cannot return machine-level monthly time-series — use get_mtbf_mttr.
    Cannot compute cross-station comparisons in one call — call per station.

    Args:
        station_id: Station identifier (e.g. 'STP-01-PRS')

    Returns:
        Formatted text summary, or TERMINAL string if station not found.
    """
    from src.datagen.factory_model import FACTORY_STATIONS
    station = FACTORY_STATIONS.get(station_id)
    if not station:
        return (
            f"TERMINAL: Station '{station_id}' not found in factory topology. "
            "Valid format: STP-01-PRS, WLD-02-SDP, ASM-01-PWR, etc. Do not retry."
        )

    results = []
    for machine in station.machines:
        metrics = ch.get_reliability_metrics(machine.machine_id, period="monthly")
        if metrics:
            n = len(metrics)
            avg_mtbf = sum(m["mtbf_hrs"] for m in metrics) / n
            avg_mttr = sum(m["mttr_hrs"] for m in metrics) / n
            avg_avail = sum(m["availability_pct"] for m in metrics) / n
            total_failures = sum(m["num_failures"] for m in metrics)
            flag = " ⚠ MOST FAILURES" if total_failures >= 10 else ""
            results.append(
                f"{machine.machine_id} ({machine.model}): "
                f"avg MTBF={avg_mtbf:.1f}h, "
                f"avg MTTR={avg_mttr:.2f}h, "
                f"avg Availability={avg_avail:.2f}%, "
                f"total failures={total_failures}{flag}"
            )

    if not results:
        return (
            f"TERMINAL: No reliability data found for any machine at station '{station_id}'. "
            "Do not retry — report that reliability data is unavailable."
        )
    return "\n".join(results)


def get_degradation_status(
    machine_id: str,
    component: str | None = None,
    hours_back: Annotated[int, Field(ge=1, le=168, description="Hours of history to retrieve (1–168). Default 24 = last day.")] = 24,
) -> list[dict] | str:
    """[ACTION]: Retrieve health index and remaining useful life (RUL) trend for a machine. [TARGET]: degradation_state table (ClickHouse).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier. component is optional;
    if None, returns all tracked components. hours_back=24 equals 1 day of history.

    [OUTPUT GUARANTEE]: Returns time-series rows with: timestamp, component, health_index
    (1.0=healthy, 0.0=failed), rul_hours. Ordered by timestamp. Use health_index < 0.5 and
    rul_hours < 100 as degradation warning thresholds.

    [NEGATIVE BOUNDARY]: Cannot return degradation predictions beyond the current RUL estimate.
    Not all machines have degradation models — empty list means no model exists for this machine.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')
        component: Specific component (e.g. 'hydraulic_pump') — optional, returns all if None
        hours_back: Hours of history (default 24 = 1 day)

    Returns:
        Degradation time-series list. TERMINAL string if no data.
    """
    data = ch.get_degradation_state(machine_id, component, hours_back)
    if not data:
        return (
            f"TERMINAL: No degradation data for machine '{machine_id}' "
            f"(component={component}, hours_back={hours_back}). "
            "This machine may not have a degradation model. Do not retry."
        )
    return data


def get_failure_rate_trend(machine_id: str) -> list[dict] | str:
    """[ACTION]: Compute monthly failure rate trend for a machine to detect degradation over time. [TARGET]: machine_reliability_metrics table (ClickHouse).

    [INPUT PREREQUISITE]: machine_id must be a valid machine identifier. Requires at least
    2 months of data for trend computation.

    [OUTPUT GUARANTEE]: Returns monthly metrics from get_mtbf_mttr enriched with additional
    fields per row: change_pct (% change from previous month), trend
    ('worsening'/>10% increase / 'improving'/<-10% / 'stable'). The first month has no change_pct.

    [NEGATIVE BOUNDARY]: Cannot predict future failure rate. Requires ≥2 months of data.
    Cannot aggregate across machines.

    Args:
        machine_id: Machine identifier (e.g. 'STP-01-PRS-HYP01')

    Returns:
        Monthly trend list with change annotations. TERMINAL string if insufficient data.
    """
    metrics = ch.get_reliability_metrics(machine_id, period="monthly")
    if not metrics:
        return (
            f"TERMINAL: No reliability metrics for machine '{machine_id}'. "
            "Verify the machine_id. Do not retry."
        )
    if len(metrics) < 2:
        return metrics

    for i in range(1, len(metrics)):
        prev = metrics[i - 1]["failure_rate"]
        curr = metrics[i]["failure_rate"]
        if prev > 0:
            change_pct = ((curr - prev) / prev) * 100
            metrics[i]["change_pct"] = round(change_pct, 1)
            metrics[i]["trend"] = "worsening" if change_pct > 10 else "improving" if change_pct < -10 else "stable"
        else:
            metrics[i]["change_pct"] = 0
            metrics[i]["trend"] = "stable"

    return metrics
