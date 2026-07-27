"""SPC and process capability tools — Cpk monitoring, control chart data."""

from src.db.clickhouse import queries as ch


def get_spc_data(
    station_id: str,
    parameter: str,
    days_back: int = 7,
) -> list[dict] | str:
    """[ACTION]: Retrieve SPC time-series data for a station parameter — used for control chart display. [TARGET]: spc_measurements table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code (e.g. 'STP-01-PRS').
    parameter must be a valid SPC parameter for that station (e.g. 'panel_thickness',
    'nugget_diameter'). Use search_specification to discover valid parameter names.

    [OUTPUT GUARANTEE]: Returns time-ordered rows with: timestamp, value, ucl, lcl, usl, lsl,
    target, cp, cpk. UCL/LCL are control limits (statistical); USL/LSL are specification limits
    (engineering). Use check_control_rules on this data to evaluate Western Electric violations.

    [NEGATIVE BOUNDARY]: Cannot return SPC data for parameters not tracked at this station.
    Limited to 1000 points per call. Does not evaluate rule violations — use check_control_rules.

    Args:
        station_id: Station identifier (e.g. 'STP-01-PRS')
        parameter: SPC parameter name (e.g. 'panel_thickness', 'nugget_diameter')
        days_back: Days of history (default 7)

    Returns:
        Time-series SPC rows. TERMINAL string if no data found.
    """
    data = ch.get_spc_data(station_id, parameter, days_back)
    if not data:
        return (
            f"TERMINAL: No SPC data for station '{station_id}', parameter '{parameter}' "
            f"(days_back={days_back}). "
            "Verify the station_id and parameter name. Do not retry."
        )
    return data


def get_cpk(
    station_id: str,
    parameter: str,
    days_back: int = 30,
) -> list[dict] | str:
    """[ACTION]: Retrieve daily Cpk trend for a station parameter — monitors process capability over time. [TARGET]: process_capability_history table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code. parameter must be a valid SPC
    parameter for that station. Use days_back=30 for monthly capability review.

    [OUTPUT GUARANTEE]: Returns daily rows with: date, cp, cpk, pp, ppk, out_of_control_signals,
    trending_alert. Cpk > 1.33 = capable; 1.0–1.33 = marginal; < 1.0 = not capable.
    Ordered by date ascending.

    [NEGATIVE BOUNDARY]: Cannot return raw measurement values — use get_spc_data for that.
    Cannot compute Cpk in real-time — returns stored daily calculations.

    Args:
        station_id: Station identifier
        parameter: SPC parameter name
        days_back: Days of history (default 30)

    Returns:
        Daily Cpk trend list. TERMINAL string if no data.
    """
    data = ch.get_process_capability(station_id, parameter, days_back)
    if not data:
        return (
            f"TERMINAL: No Cpk data for station '{station_id}', parameter '{parameter}' "
            f"(days_back={days_back}). "
            "Verify the station_id and parameter. Do not retry."
        )
    return data


def get_process_capability(
    station_id: str,
    parameter: str,
) -> dict | str:
    """[ACTION]: Retrieve the latest process capability summary (Cp, Cpk, Pp, Ppk) with pass/fail assessment. [TARGET]: process_capability_history table (ClickHouse), last 1 day.

    [INPUT PREREQUISITE]: station_id must be a valid station code. parameter must be a valid
    SPC parameter. Returns the single latest record for a quick capability snapshot.

    [OUTPUT GUARANTEE]: Returns the latest capability row enriched with an assessment string:
    'CAPABLE' (Cpk ≥ 1.33), 'MARGINAL' (1.0 ≤ Cpk < 1.33), or 'NOT CAPABLE' (Cpk < 1.0).
    Contains: date, cp, cpk, pp, ppk, out_of_control_signals, trending_alert, assessment.

    [NEGATIVE BOUNDARY]: Returns only the most recent day's snapshot — not a trend.
    Use get_cpk for a trend. Cannot return capability for non-SPC-tracked parameters.

    Args:
        station_id: Station identifier
        parameter: SPC parameter name

    Returns:
        Latest capability dict with assessment, or TERMINAL string if no data.
    """
    data = ch.get_process_capability(station_id, parameter, days_back=1)
    if not data:
        return (
            f"TERMINAL: No capability data for station '{station_id}', parameter '{parameter}'. "
            "Verify both values. Do not retry."
        )

    latest = data[-1]
    cpk = latest.get("cpk", 0)

    if cpk >= 1.33:
        assessment = "CAPABLE — process is well centered and within specification"
    elif cpk >= 1.0:
        assessment = "MARGINAL — process is capable but at risk. Investigate drift."
    else:
        assessment = "NOT CAPABLE — process cannot reliably meet specification. Immediate action required."

    latest["assessment"] = assessment
    return latest


def check_control_rules(
    station_id: str,
    parameter: str,
    days_back: int = 3,
) -> dict | str:
    """[ACTION]: Evaluate Western Electric out-of-control rules on SPC data for a station parameter. [TARGET]: spc_measurements table (ClickHouse).

    [INPUT PREREQUISITE]: station_id must be a valid station code. parameter must be a valid SPC
    parameter. Requires at least 9 data points for rules 1 and 2; at least 6 for rule 3.
    days_back should cover enough data for meaningful rule evaluation.

    [OUTPUT GUARANTEE]: Returns a dict with: station_id, parameter, data_points_checked,
    violations (list of descriptive strings for each rule triggered), status
    ('OUT OF CONTROL' or 'IN CONTROL'). Empty violations list means all rules pass.

    [NEGATIVE BOUNDARY]: Checks only Rules 1 (beyond limits), 2 (9 on one side), and 3 (6 trending).
    Does not check Rules 4–8. Returns status based on stored UCL/LCL from the data, not live limits.

    Args:
        station_id: Station identifier
        parameter: SPC parameter name
        days_back: Days of data to evaluate (default 3)

    Returns:
        Control rules evaluation dict, or message dict if insufficient data.
    """
    data = ch.get_spc_data(station_id, parameter, days_back)
    if not data:
        return (
            f"TERMINAL: No SPC data for station '{station_id}', parameter '{parameter}' "
            f"(days_back={days_back}). Verify both values. Do not retry."
        )

    if len(data) < 8:
        return {
            "station_id": station_id,
            "parameter": parameter,
            "data_points_checked": len(data),
            "violations": [],
            "status": "INSUFFICIENT DATA",
            "message": f"Only {len(data)} points — need ≥8 for meaningful rule evaluation. Increase days_back.",
        }

    values = [d["value"] for d in data]
    ucl = data[0]["ucl"]
    lcl = data[0]["lcl"]
    center = (ucl + lcl) / 2
    violations = []

    for i, v in enumerate(values):
        if v > ucl or v < lcl:
            violations.append(f"Rule 1: Point {i} ({v:.3f}) beyond control limits [{lcl:.3f}, {ucl:.3f}]")

    side = [1 if v > center else -1 for v in values]
    for i in range(len(side) - 8):
        window = side[i:i + 9]
        if all(s == window[0] for s in window):
            violations.append(
                f"Rule 2: 9 consecutive points on {'upper' if window[0] > 0 else 'lower'} "
                f"side starting at point {i}"
            )
            break

    for i in range(len(values) - 5):
        diffs = [values[i + j + 1] - values[i + j] for j in range(5)]
        if all(d > 0 for d in diffs):
            violations.append(f"Rule 3: 6 consecutive increasing points starting at {i}")
            break
        if all(d < 0 for d in diffs):
            violations.append(f"Rule 3: 6 consecutive decreasing points starting at {i}")
            break

    return {
        "station_id": station_id,
        "parameter": parameter,
        "data_points_checked": len(values),
        "violations": violations,
        "status": "OUT OF CONTROL" if violations else "IN CONTROL",
    }
