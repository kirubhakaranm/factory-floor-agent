"""Quality inspection tools — dimensional, visual, sampling, rework, defect rates."""


def get_dimensional_results(
    station_id: str,
    result_filter: str | None = None,
    limit: int = 50,
) -> str:
    """Get dimensional inspection results for a station.

    Args:
        station_id: Station identifier
        result_filter: Filter by result: 'pass' or 'fail' (optional)
        limit: Maximum results to return

    Returns:
        List of inspections with measurement_name, nominal, tolerances, actual_value, result
    """
    return (
        f"Querying dimensional inspections for {station_id} "
        f"(filter: {result_filter or 'all'}, limit: {limit}). "
        "Returns insp_id, measurement_name, nominal, upper_tol, lower_tol, actual_value, result, timestamp."
    )


def get_sampling_results(
    station_id: str,
    limit: int = 20,
) -> str:
    """Get AQL sampling inspection results for a station.

    Args:
        station_id: Station identifier
        limit: Maximum results

    Returns:
        Sampling inspections with lot_size, sample_size, aql_level, defects_found, disposition
    """
    return (
        f"Querying sampling inspections for {station_id} (limit: {limit}). "
        "Returns insp_id, lot_size, sample_size, aql_level, accept_number, "
        "defects_found, disposition (accept/reject), inspection_type."
    )


def get_visual_checklist(
    station_id: str,
    limit: int = 20,
) -> str:
    """Get visual inspection checklist results for a station.

    Args:
        station_id: Station identifier
        limit: Maximum results

    Returns:
        Visual checklists with checkpoint items and OK/NG results per item
    """
    return (
        f"Querying visual checklists for {station_id} (limit: {limit}). "
        "Returns checklist_id, checkpoint_items (dict of item:OK/NG), defect_category."
    )


def get_defect_rates(station_id: str) -> str:
    """Get overall defect rate for a station (pass/fail ratio from dimensional inspections).

    Args:
        station_id: Station identifier

    Returns:
        Total inspections, failures, defect rate percentage
    """
    return (
        f"Querying defect rates for {station_id}. "
        "Returns total inspections, fail count, defect_rate (%), first_pass_yield (%)."
    )


def get_rework_history(
    station_id: str,
    limit: int = 30,
) -> str:
    """Get rework records for a station — parts that failed inspection and were reworked.

    Args:
        station_id: Station identifier
        limit: Maximum results

    Returns:
        Rework records with defect_type, rework_action, rework_time_min, re_inspect_result, cost
    """
    return (
        f"Querying rework history for {station_id} (limit: {limit}). "
        "Returns rework_id, defect_type, rework_action, rework_time_min, "
        "re_inspect_result (pass/fail after rework), cost."
    )
