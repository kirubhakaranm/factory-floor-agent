"""Reliability metrics tools — MTBF, MTTR, availability, failure rate trends."""

from src.db.clickhouse import queries as ch


def get_mtbf_mttr(machine_id: str) -> list[dict]:
    """Get monthly MTBF and MTTR metrics for a machine.

    Args:
        machine_id: Machine identifier

    Returns:
        Monthly reliability metrics: mtbf_hrs, mttr_hrs, availability_pct, failure_rate, num_failures
    """
    return ch.get_reliability_metrics(machine_id, period="monthly")


def get_reliability_report(station_id: str) -> str:
    """Get a reliability summary for all machines at a station.

    Args:
        station_id: Station identifier (e.g., 'STP-01-PRS')

    Returns:
        Per-machine MTBF, MTTR, availability, and reliability score for the last period
    """
    from src.datagen.factory_model import FACTORY_STATIONS
    station = FACTORY_STATIONS.get(station_id)
    if not station:
        return f"Station {station_id} not found"

    results = []
    for machine in station.machines:
        metrics = ch.get_reliability_metrics(machine.machine_id, period="monthly")
        if metrics:
            latest = metrics[-1]
            results.append(
                f"{machine.machine_id} ({machine.model}): "
                f"MTBF={latest['mtbf_hrs']:.0f}hrs, "
                f"MTTR={latest['mttr_hrs']:.1f}hrs, "
                f"Availability={latest['availability_pct']:.1f}%, "
                f"Failures={latest['num_failures']}, "
                f"Score={latest['reliability_score']:.0f}/100"
            )

    return "\n".join(results) if results else f"No reliability data for {station_id}"


def get_degradation_status(
    machine_id: str,
    component: str | None = None,
    hours_back: int = 168,
) -> list[dict]:
    """Get health index and remaining useful life (RUL) trend for a machine component.

    Args:
        machine_id: Machine identifier
        component: Specific component to check (e.g., 'hydraulic_pump'). If None, returns all.
        hours_back: Hours of history (default 168 = 1 week)

    Returns:
        Time-series of health_index (1.0=healthy, 0.0=failed) and rul_hours
    """
    return ch.get_degradation_state(machine_id, component, hours_back)


def get_failure_rate_trend(machine_id: str) -> list[dict]:
    """Get monthly failure rate trend for a machine to identify degradation.

    Args:
        machine_id: Machine identifier

    Returns:
        Monthly failure rates with trend direction
    """
    metrics = ch.get_reliability_metrics(machine_id, period="monthly")
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
