"""VIN traceability tools — trace a vehicle's complete production history."""

from src.db.postgres import queries as pg


def trace_vin_history(vin_id: str) -> dict | str:
    """[ACTION]: Retrieve the complete production trail for a vehicle by VIN. [TARGET]: vin_registry, production_batches, finished_goods, sampling_inspections (Postgres).

    [INPUT PREREQUISITE]: vin_id must be a valid PrimeEV VIN in format PEF-{MODEL}-{YY}-{XXXXXX}
    (e.g. 'PEF-SD100-26-002000'). MODEL is SD100, SV200, or CP300.

    [OUTPUT GUARANTEE]: Returns a dict with four sections:
    - vin: registry record (vin_id, model_id, model_name, production_date, batch_id, status)
    - batch: production batch stats (units_produced, units_passed, batch_yield_pct, start_time, end_time)
    - finished_goods: completion_date, storage_location, ship_date (null if not shipped)
    - station_quality_context: all sampling inspection rows from the VIN's production date
    - note: explaining that quality is tracked at batch/station level, not per individual unit

    [NEGATIVE BOUNDARY]: Cannot return per-unit dimensional inspection results — dimensional
    inspections have vin_id=NULL and are batch-level. Use get_vin_quality_summary for a
    stage-level quality scorecard. Cannot trace sub-component lot provenance — use
    get_component_consumption for that.

    Args:
        vin_id: Vehicle Identification Number (e.g. 'PEF-SD100-26-002000')

    Returns:
        Production trail dict, or TERMINAL string if VIN not found.
    """
    result = pg.sync_get_vin_history(vin_id)
    if isinstance(result, dict) and result.get("error"):
        return (
            f"TERMINAL: {result['error']}. "
            "Verify the VIN format: PEF-SD100-26-002000. Do not retry with a guessed VIN."
        )
    return result


def get_vin_quality_summary(vin_id: str) -> dict | str:
    """[ACTION]: Retrieve a quality scorecard for a vehicle — batch yield and per-stage sampling pass/fail on production date. [TARGET]: vin_registry, production_batches, sampling_inspections, finished_goods (Postgres).

    [INPUT PREREQUISITE]: vin_id must be a valid PrimeEV VIN. Call this after trace_vin_history
    to get the quality scorecard. The VIN must exist in the registry.

    [OUTPUT GUARANTEE]: Returns a dict with:
    - vin_id, model, production_date, status, batch_id
    - batch_yield: units_produced, units_passed, batch_yield_pct for the VIN's batch
    - stage_quality_on_production_date: per-stage (STP/WLD/PNT/ASM/QAT) aggregated sampling
      inspection counts (lots accepted/rejected, total defects)
    - final_disposition: completion_date, storage_location, ship_date

    [NEGATIVE BOUNDARY]: Same as trace_vin_history — quality is batch/station level, not per unit.
    This is a quality scorecard view; for the full production trail, use trace_vin_history.

    Args:
        vin_id: Vehicle Identification Number (e.g. 'PEF-SD100-26-002000')

    Returns:
        Quality scorecard dict, or TERMINAL string if VIN not found.
    """
    result = pg.sync_get_vin_quality_summary(vin_id)
    if isinstance(result, dict) and result.get("error"):
        return (
            f"TERMINAL: {result['error']}. "
            "Verify the VIN format: PEF-SD100-26-002000. Do not retry with a guessed VIN."
        )
    return result
