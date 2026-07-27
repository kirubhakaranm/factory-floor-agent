"""Quality inspection tools — dimensional, visual, sampling, rework, defect rates,
defect catalog, inspection plans, AQL recommendations, and measurement specs."""

from typing import Annotated, Literal

from pydantic import Field

from src.db.postgres import queries as pg


def get_dimensional_results(
    station_id: str,
    result_filter: Literal["pass", "fail"] | None = None,
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum results (1–500)")] = 50,
) -> list[dict]:
    """[ACTION]: Retrieve dimensional inspection results for a station. [TARGET]: dimensional_inspections table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'STP-01-PRS').
    result_filter must be 'pass' or 'fail' if provided. Use get_measurement_specs to understand
    the tolerance limits before interpreting results.

    [OUTPUT GUARANTEE]: Returns inspection rows with: insp_id, station_id, measurement_name,
    nominal, upper_tol, lower_tol, actual_value, result, timestamp. Ordered newest-first.
    Note: vin_id is NULL in dimensional_inspections — quality is tracked at batch/station level.

    [NEGATIVE BOUNDARY]: Cannot return per-VIN inspection results — dimensional inspections
    are batch-level. Cannot return AQL sampling results — use get_sampling_results.
    Cannot return visual checklist results — use get_visual_checklist.

    Args:
        station_id: Station identifier (e.g. 'STP-01-PRS')
        result_filter: Filter by result: 'pass' or 'fail' (optional)
        limit: Maximum results (default 50)

    Returns:
        List of dimensional inspection dicts.
    """
    return pg.sync_get_dimensional_results(station_id, result_filter, limit)


def get_sampling_results(
    station_id: str,
    limit: Annotated[int, Field(ge=1, le=200, description="Maximum results (1–200)")] = 20,
) -> list[dict]:
    """[ACTION]: Retrieve AQL sampling inspection results for a station — lot accept/reject decisions. [TARGET]: sampling_inspections table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'WLD-01-UBD').
    Use get_aql_recommendation to understand what sample size and accept number should have been used.

    [OUTPUT GUARANTEE]: Returns sampling rows with: insp_id, station_id, lot_number, lot_size,
    sample_size, aql_level, accept_number, reject_number, defects_found, disposition
    (accept/reject/conditional), inspection_type (visual/functional/destructive), timestamp.
    Ordered newest-first.

    [NEGATIVE BOUNDARY]: Cannot return dimensional measurement values — use get_dimensional_results.
    Cannot return individual unit defects — use get_visual_checklist.

    Args:
        station_id: Station identifier
        limit: Maximum results (default 20)

    Returns:
        List of sampling inspection dicts.
    """
    return pg.sync_get_sampling_results(station_id, limit)


def get_visual_checklist(
    station_id: str,
    limit: Annotated[int, Field(ge=1, le=200, description="Maximum results (1–200)")] = 20,
) -> list[dict]:
    """[ACTION]: Retrieve visual inspection checklist results for a station. [TARGET]: visual_checklists table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'ASM-03-FNL').

    [OUTPUT GUARANTEE]: Returns checklist rows with: checklist_id, vin_id, station_id,
    checkpoint_items (dict of item_name → 'OK'/'NG'/'NA'), defect_category, timestamp.
    Ordered newest-first.

    [NEGATIVE BOUNDARY]: Cannot return dimensional measurements — use get_dimensional_results.
    Cannot return AQL lot decisions — use get_sampling_results.

    Args:
        station_id: Station identifier
        limit: Maximum results (default 20)

    Returns:
        List of visual checklist dicts.
    """
    return pg.sync_get_visual_checklist(station_id, limit)


def get_defect_rates(station_id: str) -> dict:
    """[ACTION]: Compute overall defect rate (pass/fail ratio) from dimensional inspections for a station. [TARGET]: dimensional_inspections table (Postgres), aggregated.

    [INPUT PREREQUISITE]: station_id must be a valid station code. Returns a YTD aggregate
    over all dimensional inspections for the station.

    [OUTPUT GUARANTEE]: Returns a single dict with: total_inspections, fail_count,
    defect_rate_pct (0.0–100.0), first_pass_yield_pct (100 - defect_rate).
    An empty dict means no dimensional inspections exist for this station.

    [NEGATIVE BOUNDARY]: Only covers dimensional inspection data — not visual or sampling.
    Cannot return trend over time — use get_dimensional_results with time filtering for that.
    Cannot break down by defect type — use get_rework_history for defect-type breakdown.

    Args:
        station_id: Station identifier

    Returns:
        Aggregate defect rate dict.
    """
    return pg.sync_get_defect_rates(station_id)


def get_rework_history(
    station_id: str,
    limit: Annotated[int, Field(ge=1, le=300, description="Maximum results (1–300)")] = 30,
) -> list[dict]:
    """[ACTION]: Retrieve rework records for a station — units that failed inspection and were reworked. [TARGET]: rework_records table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code.

    [OUTPUT GUARANTEE]: Returns rework rows with: rework_id, vin_id, station_id, defect_type,
    rework_action, rework_time_min, re_inspect_result (pass/fail after rework), cost, timestamp.
    Ordered newest-first.

    [NEGATIVE BOUNDARY]: Cannot return scrap records — those are units scrapped, not reworked.
    Cannot return the original dimensional inspection that triggered the rework.

    Args:
        station_id: Station identifier
        limit: Maximum results (default 30)

    Returns:
        List of rework record dicts.
    """
    return pg.sync_get_rework_history(station_id, limit)


def get_defect_catalog(
    station_id: str | None = None,
    stage: Literal["STP", "WLD", "PNT", "ASM", "QAT"] | None = None,
    severity: Literal["critical", "major", "minor"] | None = None,
    category: Literal["structural", "cosmetic", "functional", "safety"] | None = None,
) -> list[dict]:
    """[ACTION]: Look up the defect master catalog — all named defects with severity and detection method. [TARGET]: defect_codes table (Postgres).

    [INPUT PREREQUISITE]: All filters are optional. stage must be a 3-letter stage code if provided.
    severity and category must be Literal values if provided.

    [OUTPUT GUARANTEE]: Returns defect rows with: defect_code, name, stage, station_id, category,
    severity, detection_method, description. Ordered by station_id, severity (critical first), name.
    Empty list means no defects match the filter — not a data error.

    [NEGATIVE BOUNDARY]: Returns reference data only — not actual occurrence counts from inspections.
    To see how often a defect type occurred, use get_rework_history or get_dimensional_results.

    Args:
        station_id: Filter by station (optional, e.g. 'WLD-01-UBD')
        stage: Filter by stage code (optional): 'STP', 'WLD', 'PNT', 'ASM', or 'QAT'
        severity: Filter by severity (optional): 'critical', 'major', or 'minor'
        category: Filter by category (optional): 'structural', 'cosmetic', 'functional', or 'safety'

    Returns:
        List of defect catalog dicts.
    """
    return pg.sync_get_defect_catalog(station_id, stage, severity, category)


def get_inspection_plan(station_id: str) -> list[dict]:
    """[ACTION]: Retrieve the formal inspection plan for a station — what is checked, how, and how often. [TARGET]: inspection_plans table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'ASM-01-PWR').
    Use this before diagnosing quality issues to understand whether the problem is a coverage gap
    (characteristic not being checked) vs. process drift (something failing more often).

    [OUTPUT GUARANTEE]: Returns plan rows with: plan_id, station_id, characteristic_name,
    inspection_type, measurement_method, frequency, sample_size_pct, control_chart_enabled,
    responsible_role. Empty list means no formal inspection plan exists for this station.

    [NEGATIVE BOUNDARY]: Returns the plan definition, not actual inspection results.
    To see results, use get_dimensional_results, get_sampling_results, or get_visual_checklist.

    Args:
        station_id: Station identifier (e.g. 'ASM-01-PWR')

    Returns:
        List of inspection plan rows.
    """
    return pg.sync_get_inspection_plan(station_id)


def get_aql_recommendation(
    lot_size: int,
    inspection_level: Literal["normal", "tightened", "reduced"] = "normal",
) -> dict | str:
    """[ACTION]: Look up the AQL sampling plan for a given lot size and inspection level (ISO 2859-1). [TARGET]: aql_schemes table (Postgres).

    [INPUT PREREQUISITE]: lot_size must be a positive integer. inspection_level must be one of the
    Literal values. 'normal' = AQL 1.0%, 'tightened' = AQL 0.65% (after failures), 'reduced' = AQL 2.5%.

    [OUTPUT GUARANTEE]: Returns a single dict with: scheme_id, inspection_level, aql_percent,
    lot_size_min, lot_size_max, sample_size, accept_number, reject_number, sample_code.
    Use accept_number and reject_number to make the disposition decision.

    [NEGATIVE BOUNDARY]: Returns one AQL row — not a comparison across levels.
    Cannot return skip-lot or continuous sampling plans.

    Args:
        lot_size: Number of units in the lot
        inspection_level: AQL level: 'normal', 'tightened', or 'reduced'

    Returns:
        AQL plan dict, or TERMINAL string if no matching scheme found.
    """
    result = pg.sync_get_aql_recommendation(lot_size, inspection_level)
    if not result:
        return (
            f"TERMINAL: No AQL scheme found for lot_size={lot_size}, "
            f"inspection_level='{inspection_level}'. "
            "Verify the lot_size is within supported ranges. Do not retry."
        )
    return result


def get_measurement_specs(
    station_id: str,
    measurement_name: str | None = None,
) -> list[dict]:
    """[ACTION]: Retrieve engineering measurement specifications (nominal + tolerances) for a station. [TARGET]: measurement_specs table (Postgres).

    [INPUT PREREQUISITE]: station_id must be a valid station code. measurement_name is optional;
    if omitted, returns all active specs for the station. Only returns currently active specs
    (superseded_date IS NULL).

    [OUTPUT GUARANTEE]: Returns spec rows with: spec_id, station_id, measurement_name, nominal,
    upper_tol, lower_tol, usl, lsl, effective_date, drawing_ref. Empty list means no active spec
    exists for this station/characteristic.

    [NEGATIVE BOUNDARY]: Does not return actual inspection results — use get_dimensional_results
    to compare against these specs. Cannot return historical/superseded specs.

    Args:
        station_id: Station identifier
        measurement_name: Specific characteristic (e.g. 'dim_3') — optional, returns all if omitted

    Returns:
        List of active measurement spec dicts.
    """
    return pg.sync_get_measurement_specs(station_id, measurement_name)
