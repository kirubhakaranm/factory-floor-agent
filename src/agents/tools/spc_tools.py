"""SPC and process capability tools — Cpk monitoring, control chart data."""

from src.db.clickhouse import queries as ch


def get_spc_data(
    station_id: str,
    parameter: str,
    days_back: int = 7,
) -> list[dict]:
    """Get SPC measurement data for control chart display.

    Args:
        station_id: Station identifier (e.g., 'STP-01-PRS')
        parameter: Parameter name (e.g., 'panel_thickness', 'nugget_diameter')
        days_back: Days of history

    Returns:
        Time-series of value, UCL, LCL, USL, LSL, target, Cp, Cpk
    """
    return ch.get_spc_data(station_id, parameter, days_back)


def get_cpk(
    station_id: str,
    parameter: str,
    days_back: int = 30,
) -> list[dict]:
    """Get daily Cpk trend for a station parameter — used to monitor process capability over time.

    Args:
        station_id: Station identifier
        parameter: Parameter name
        days_back: Days of history

    Returns:
        Daily Cpk values with trend. Cpk > 1.33 is good, < 1.0 is out of control.
    """
    return ch.get_process_capability(station_id, parameter, days_back)


def get_process_capability(
    station_id: str,
    parameter: str,
) -> dict:
    """Get current process capability summary (latest Cp, Cpk, Pp, Ppk) with assessment.

    Args:
        station_id: Station identifier
        parameter: Parameter name

    Returns:
        Latest capability indices with pass/fail assessment
    """
    data = ch.get_process_capability(station_id, parameter, days_back=1)
    if not data:
        return {"error": f"No capability data for {station_id}/{parameter}"}

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
) -> dict:
    """Check Western Electric rules for out-of-control conditions on SPC data.

    Args:
        station_id: Station identifier
        parameter: Parameter name
        days_back: Days of data to check

    Returns:
        List of rule violations found (if any)
    """
    data = ch.get_spc_data(station_id, parameter, days_back)
    if len(data) < 8:
        return {"violations": [], "message": "Insufficient data for rule checking"}

    values = [d["value"] for d in data]
    ucl = data[0]["ucl"]
    lcl = data[0]["lcl"]
    center = (ucl + lcl) / 2

    violations = []

    # Rule 1: Point beyond 3-sigma (UCL/LCL)
    for i, v in enumerate(values):
        if v > ucl or v < lcl:
            violations.append(f"Rule 1: Point {i} ({v:.3f}) beyond control limits [{lcl:.3f}, {ucl:.3f}]")

    # Rule 2: 9 consecutive points on same side of center
    side = [1 if v > center else -1 for v in values]
    for i in range(len(side) - 8):
        window = side[i:i + 9]
        if all(s == window[0] for s in window):
            violations.append(f"Rule 2: 9 consecutive points on {'upper' if window[0] > 0 else 'lower'} side starting at point {i}")
            break

    # Rule 3: 6 consecutive points trending in same direction
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
