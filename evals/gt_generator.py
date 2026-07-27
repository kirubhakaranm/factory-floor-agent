"""Ground Truth Generator — queries the actual databases and populates
key_facts.data in eval case JSON files with exact numbers.

Why this exists:
  Generic key_facts like "OEE should be around 75%" let wrong answers pass.
  Exact key_facts like "OEE at ASM-01-PWR on 2026-06-30 was 74.2%" catch them.

How it works:
  1. Finds each eval case that has an empty key_facts.data list.
  2. Calls the same DB query functions the agent tools call.
  3. Extracts the relevant numbers and formats them as fact strings.
  4. Writes the populated data back into the eval case JSON file.

Since the dataset is deterministic (seed=42), running this once after
seeding the DB gives stable ground truth that never changes unless you
regenerate the data.

Usage:
  python -m evals.gt_generator                  # populate all cases
  python -m evals.gt_generator --case PR-001    # one specific case
  python -m evals.gt_generator --dry-run        # print without writing
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

EVAL_DIR = Path(__file__).parent / "evalsets"


# ── ClickHouse helpers ──────────────────────────────────────────────────────

def _ch() -> object:
    """Return the ClickHouse sync client."""
    from src.db.clickhouse.client import get_clickhouse_client
    return get_clickhouse_client()


def _ch_query(sql: str) -> list[dict]:
    """Execute a ClickHouse SQL query and return rows as a list of dicts."""
    from src.db.clickhouse.client import query
    return query(sql)


# ── Postgres helpers ────────────────────────────────────────────────────────

def _pg_query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a Postgres SQL query with optional params and return rows as dicts."""
    from src.db.postgres.queries import _q
    return _q(sql, params or {})


# ── Anchor: latest date in each ClickHouse table ───────────────────────────

def _ch_max_date(table: str) -> str:
    """Return the latest date string (YYYY-MM-DD) present in a ClickHouse table."""
    rows = _ch_query(f"SELECT toDate(max(timestamp)) AS d FROM primeev_telemetry.{table}")
    return str(rows[0]["d"]) if rows else "2026-06-30"


def _pg_max_date(table: str, date_col: str = "created_at") -> str:
    """Return the latest date string (YYYY-MM-DD) present in a Postgres table."""
    rows = _pg_query(f"SELECT DATE(MAX({date_col})) AS d FROM {table}")
    return str(rows[0]["d"]) if rows else "2026-06-30"


# ── Per-case ground truth query functions ──────────────────────────────────
# Each function returns a list of exact fact strings to store in key_facts.data.

def _gt_eq001() -> list[str]:
    """EQ-001: Press 1 hydraulic oil temperature — latest reading."""
    anchor = _ch_max_date("sensor_readings")
    rows = _ch_query(f"""
        SELECT argMax(value, timestamp) AS temp_c, any(unit) AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'STP-01-PRS-HYP01' AND sensor_type = 'TMP'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 2 HOUR
    """)
    if not rows or rows[0]["temp_c"] is None:
        return []
    temp = round(float(rows[0]["temp_c"]), 1)
    unit = rows[0]["unit"] or "C"
    status = "EXCEEDS maximum of 65°C" if temp > 65 else "within normal range (35–65°C)"
    return [
        f"Latest hydraulic oil temperature at STP-01-PRS-HYP01 is {temp}°{unit}",
        f"Temperature status: {status}",
        "Normal operating range is 35–65°C for hydraulic presses",
    ]


def _gt_eq002() -> list[str]:
    """EQ-002: Press 1 MTBF/MTTR this month (reliability metrics only).

    get_failure_history is a stub tool — failure counts from Postgres won't
    appear in agent responses yet. Only ClickHouse reliability metrics are
    populated here since get_mtbf_mttr is a real tool.
    """
    rel = _ch_query("""
        SELECT mtbf_hrs, mttr_hrs, availability_pct, num_failures
        FROM primeev_telemetry.machine_reliability_metrics
        WHERE machine_id = 'STP-01-PRS-HYP01' AND period = 'monthly'
        ORDER BY period_start DESC LIMIT 1
    """)
    if not rel:
        return []
    return [
        f"STP-01-PRS-HYP01 current MTBF: {round(float(rel[0]['mtbf_hrs']), 1)} hours",
        f"STP-01-PRS-HYP01 current MTTR: {round(float(rel[0]['mttr_hrs']), 1)} hours",
        f"Machine availability: {round(float(rel[0]['availability_pct']), 1)}%",
        f"Failures this month: {rel[0]['num_failures']}",
    ]


def _gt_eq003() -> list[str]:
    """EQ-003: Hydraulic pump degradation state / RUL — latest per component."""
    rows = _ch_query("""
        SELECT component, health_index, rul_hours
        FROM primeev_telemetry.degradation_state
        WHERE machine_id = 'STP-01-PRS-HYP01'
        ORDER BY component, timestamp DESC
        LIMIT 1 BY component
    """)
    if not rows:
        return []
    facts = []
    for r in rows:
        hi = round(float(r["health_index"]), 3)
        rul = round(float(r["rul_hours"]), 0)
        facts.append(
            f"Component '{r['component']}': health_index={hi}, "
            f"remaining useful life={int(rul)} hours"
        )
    return facts


def _gt_eq004() -> list[str]:
    """EQ-004: Reliability report for all Stamping stage machines — aggregated across all months."""
    rows = _ch_query("""
        SELECT
            machine_id,
            sum(num_failures) AS total_failures,
            round(avg(mtbf_hrs), 1) AS avg_mtbf,
            round(avg(mttr_hrs), 2) AS avg_mttr,
            round(avg(availability_pct), 2) AS avg_avail
        FROM primeev_telemetry.machine_reliability_metrics
        WHERE machine_id IN (
            'STP-01-PRS-HYP01', 'STP-01-PRS-HYP02',
            'STP-02-PRS-SRV01',
            'STP-03-TRM-SRV01', 'STP-03-TRM-SRV02'
        )
          AND period = 'monthly'
        GROUP BY machine_id
        ORDER BY avg_mtbf ASC
    """)
    facts = []
    for r in rows:
        mtbf = round(float(r["avg_mtbf"]), 1)
        mttr = round(float(r["avg_mttr"]), 2)
        avail = round(float(r["avg_avail"]), 2)
        n = int(r["total_failures"])
        flag = " ⚠ MOST FAILURES" if n >= 5 else ""
        facts.append(
            f"{r['machine_id']}: avg MTBF={mtbf}h, avg MTTR={mttr}h, "
            f"avg Availability={avail}%, total failures={n}{flag}"
        )
    return facts


def _gt_eq005() -> list[str]:
    """EQ-005: Energy consumption trend for STP-01-PRS."""
    anchor = _ch_max_date("energy_consumption")
    rows = _ch_query(f"""
        SELECT toDate(ts) AS day,
               round(avg(avg_power_kw), 1) AS avg_kw,
               round(max(peak_power_kw), 1) AS peak_kw
        FROM (
            SELECT toStartOfHour(timestamp) AS ts,
                   avg(power_kw) AS avg_power_kw,
                   max(power_kw) AS peak_power_kw
            FROM primeev_telemetry.energy_consumption
            WHERE station_id = 'STP-01-PRS'
              AND timestamp >= toDateTime('{anchor}') - INTERVAL 7 DAY
            GROUP BY ts
        )
        GROUP BY day ORDER BY day
    """)
    if not rows:
        return []
    avg_kws = [float(r["avg_kw"]) for r in rows]
    trend = "rising" if avg_kws[-1] > avg_kws[0] * 1.05 else \
            "falling" if avg_kws[-1] < avg_kws[0] * 0.95 else "stable"
    overall_avg = round(sum(avg_kws) / len(avg_kws), 1)
    peak = max(float(r["peak_kw"]) for r in rows)
    return [
        f"STP-01-PRS average power draw last 7 days: {overall_avg} kW",
        f"STP-01-PRS peak power this week: {round(peak, 1)} kW",
        f"Energy consumption trend: {trend}",
    ]


def _gt_pr001() -> list[str]:
    """PR-001: Assembly stage OEE — last 7 days average."""
    anchor = _ch_max_date("oee_metrics")
    rows = _ch_query(f"""
        SELECT station_id,
               round(avg(availability) * 100, 1) AS avail_pct,
               round(avg(performance) * 100, 1)  AS perf_pct,
               round(avg(quality) * 100, 1)      AS qual_pct,
               round(avg(oee) * 100, 1)          AS oee_pct
        FROM primeev_telemetry.oee_metrics
        WHERE station_id IN ('ASM-01-PWR', 'ASM-02-INT', 'ASM-03-FNL')
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 7 DAY
        GROUP BY station_id
        ORDER BY station_id
    """)
    if not rows:
        return []
    facts = []
    for r in rows:
        vs_target = "below" if float(r["oee_pct"]) < 75 else "above"
        facts.append(
            f"{r['station_id']} OEE: {r['oee_pct']}% "
            f"(Availability {r['avail_pct']}%, Performance {r['perf_pct']}%, "
            f"Quality {r['qual_pct']}%) — {vs_target} 75% target"
        )
    return facts


def _gt_pr002() -> list[str]:
    """PR-002: Day vs Night shift OEE comparison — ASM stage, last 30 days."""
    anchor = _ch_max_date("oee_metrics")
    rows = _ch_query(f"""
        SELECT shift,
               round(avg(oee) * 100, 1)          AS avg_oee,
               round(avg(availability) * 100, 1)  AS avg_avail,
               round(avg(performance) * 100, 1)   AS avg_perf,
               count() AS data_points
        FROM primeev_telemetry.oee_metrics
        WHERE station_id IN ('ASM-01-PWR', 'ASM-02-INT', 'ASM-03-FNL')
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 30 DAY
        GROUP BY shift
        ORDER BY shift
    """)
    if not rows:
        return []
    facts = []
    for r in rows:
        facts.append(
            f"{r['shift']} shift average OEE: {r['avg_oee']}% "
            f"(Availability {r['avg_avail']}%, Performance {r['avg_perf']}%)"
        )
    if len(rows) >= 2:
        oees = {r["shift"]: float(r["avg_oee"]) for r in rows}
        shifts = list(oees.keys())
        diff = abs(oees[shifts[0]] - oees[shifts[1]])
        better = max(oees, key=oees.get)
        facts.append(f"Difference between shifts: {round(diff, 1)} percentage points — {better} shift performs better")
    return facts


# _gt_pr003 defined later in the expansion section


def _gt_qa001() -> list[str]:
    """QA-001: Cpk trend for STP-01-PRS — panel thickness parameter."""
    anchor = _ch_max_date("process_capability_history")
    rows = _ch_query(f"""
        SELECT toDate(timestamp) AS day, round(cpk, 3) AS cpk, round(cp, 3) AS cp,
               out_of_control_signals, trending_alert
        FROM primeev_telemetry.process_capability_history
        WHERE station_id = 'STP-01-PRS' AND parameter = 'panel_thickness'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 14 DAY
        ORDER BY timestamp DESC LIMIT 14
    """)
    if not rows:
        return []
    latest = rows[0]
    cpk = float(latest["cpk"])
    status = "capable" if cpk >= 1.33 else "marginal" if cpk >= 1.0 else "NOT CAPABLE"
    trend_vals = [float(r["cpk"]) for r in rows]
    direction = (
        "declining" if trend_vals[0] < trend_vals[-1] * 0.97
        else "improving" if trend_vals[0] > trend_vals[-1] * 1.03
        else "stable"
    )
    facts = [
        f"Latest Cpk for panel_thickness at STP-01-PRS: {cpk} — {status}",
        f"Cp: {float(latest['cp']):.3f}",
        f"Cpk trend over last 14 days: {direction}",
    ]
    if latest["out_of_control_signals"]:
        facts.append(f"Active out-of-control signals: {latest['out_of_control_signals']}")
    return facts


def _gt_pr007() -> list[str]:
    """PR-007: Cycle times for ASM-02-INT vs target."""
    rows = _pg_query("""
        SELECT
            station_id,
            ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time))), 1) AS avg_cycle_sec,
            COUNT(*) AS batch_count
        FROM production_batches
        WHERE station_id = 'ASM-02-INT'
        GROUP BY station_id
    """)
    if not rows:
        return []
    avg = float(rows[0]["avg_cycle_sec"])
    vs_target = "above" if avg > 240 else "at or below"
    facts = [
        f"ASM-02-INT average batch cycle time: {avg} seconds (target: 240 seconds)",
        f"Cycle time is {vs_target} target — {'potential bottleneck' if avg > 240 else 'not a bottleneck'}",
    ]
    return facts


def _gt_eq014() -> list[str]:
    """EQ-014: Vibration trend for WLD-01-UBD-RBT02 — last 48 hours."""
    anchor = _ch_max_date("sensor_readings")
    rows = _ch_query(f"""
        SELECT
            round(avg(value), 3)  AS mean_vib,
            round(max(value), 3)  AS max_vib,
            any(unit)             AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'WLD-01-UBD-RBT02'
          AND sensor_type = 'VIB'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 48 HOUR
    """)
    if not rows or rows[0]["mean_vib"] is None:
        return []
    mean_v = round(float(rows[0]["mean_vib"]), 3)
    max_v = round(float(rows[0]["max_vib"]), 3)
    unit = rows[0]["unit"] or "mm/s"
    halves = _ch_query(f"""
        SELECT
            if(timestamp >= toDateTime('{anchor}') - INTERVAL 24 HOUR, 'recent', 'earlier') AS window,
            round(avg(value), 3) AS avg_vib
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'WLD-01-UBD-RBT02'
          AND sensor_type = 'VIB'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 48 HOUR
        GROUP BY window
    """)
    half_map = {r["window"]: float(r["avg_vib"]) for r in halves}
    earlier = half_map.get("earlier", mean_v)
    recent = half_map.get("recent", mean_v)
    trend = "rising" if recent > earlier * 1.05 else \
            "falling" if recent < earlier * 0.95 else "stable"
    status = "ABOVE" if max_v > 2.0 else "within"
    return [
        f"WLD-01-UBD-RBT02 vibration mean last 48h: {mean_v} {unit}",
        f"WLD-01-UBD-RBT02 vibration peak last 48h: {max_v} {unit}",
        f"Vibration trend (48h): {trend}",
        f"Peak is {status} safe limit of 2.0 mm/s per Fanuc specification",
    ]


def _gt_qa009() -> list[str]:
    """QA-009: Cpk for nugget_diameter at WLD-01-UBD."""
    rows = _ch_query("""
        SELECT round(cpk, 3) AS cpk, round(cp, 3) AS cp, out_of_control_signals
        FROM primeev_telemetry.process_capability_history
        WHERE station_id = 'WLD-01-UBD' AND parameter = 'nugget_diameter'
        ORDER BY timestamp DESC LIMIT 1
    """)
    if not rows:
        return []
    cpk = float(rows[0]["cpk"])
    cp = float(rows[0]["cp"])
    ooc = rows[0]["out_of_control_signals"]
    status = "capable" if cpk >= 1.33 else "marginal — corrective action required" if cpk >= 1.0 else "NOT CAPABLE"
    facts = [
        f"Latest Cpk for nugget_diameter at WLD-01-UBD: {cpk} — {status}",
        f"Cp: {cp}",
    ]
    if ooc:
        facts.append(f"Active out-of-control signals: {ooc}")
    return facts


def _gt_im006() -> list[str]:
    """IM-006: Defect rate trend at WLD-01-UBD — 90-day window from Postgres."""
    # Overall defect rate (all time, matches sync_get_defect_rates)
    overall = _pg_query("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END) AS fails,
            ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS defect_rate_pct,
            ROUND(100.0*SUM(CASE WHEN result='pass' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS fpy_pct
        FROM dimensional_inspections
        WHERE station_id = 'WLD-01-UBD'
    """)
    if not overall:
        return []
    o = overall[0]
    rate = float(o["defect_rate_pct"] or 0)
    fpy = float(o["fpy_pct"] or 0)
    monthly = _pg_query("""
        SELECT
            DATE_TRUNC('month', timestamp)::date AS month,
            ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS defect_rate_pct
        FROM dimensional_inspections
        WHERE station_id = 'WLD-01-UBD'
          AND timestamp >= NOW() - INTERVAL '90 days'
        GROUP BY 1 ORDER BY 1
    """)
    trend = "stable"
    if len(monthly) >= 2:
        first = float(monthly[0]["defect_rate_pct"] or 0)
        last = float(monthly[-1]["defect_rate_pct"] or 0)
        trend = "improving" if last < first * 0.97 else "worsening" if last > first * 1.03 else "stable"
    return [
        f"WLD-01-UBD overall defect rate: {rate}% (FPY: {fpy}%)",
        f"Total inspections at WLD-01-UBD: {o['total']}",
        f"Defect rate trend over last 90 days: {trend}",
    ]


def _gt_ac009() -> list[str]:
    """AC-009: Hydraulic pressure and temperature sensor trend for STP-01-PRS-HYP01."""
    anchor = _ch_max_date("sensor_readings")
    rows = _ch_query(f"""
        SELECT
            sensor_type,
            round(avg(value), 2) AS mean_val,
            round(max(value), 2) AS max_val,
            any(unit)            AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'STP-01-PRS-HYP01'
          AND sensor_type IN ('PRS', 'TMP')
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 7 DAY
        GROUP BY sensor_type
        ORDER BY sensor_type
    """)
    if not rows:
        return []
    facts = []
    for r in rows:
        st = r["sensor_type"]
        mean = float(r["mean_val"])
        peak = float(r["max_val"])
        unit = r["unit"] or ("bar" if st == "PRS" else "C")
        label = "Hydraulic pressure" if st == "PRS" else "Hydraulic oil temperature"
        facts.append(f"STP-01-PRS-HYP01 {label} last 7 days — mean: {mean} {unit}, peak: {peak} {unit}")
    return facts


# ── Equipment ──────────────────────────────────────────────────────────────

def _gt_eq006() -> list[str]:
    """EQ-006: WLD-01-UBD-RBT01 vibration trend — 48h window."""
    anchor = _ch_max_date("sensor_readings")
    rows = _ch_query(f"""
        SELECT round(avg(value), 3) AS mean_vib, round(max(value), 3) AS max_vib, any(unit) AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'WLD-01-UBD-RBT01' AND sensor_type = 'VIB'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 48 HOUR
    """)
    if not rows or rows[0]["mean_vib"] is None:
        return []
    mean_v = round(float(rows[0]["mean_vib"]), 3)
    max_v = round(float(rows[0]["max_vib"]), 3)
    unit = rows[0]["unit"] or "mm/s"
    halves = _ch_query(f"""
        SELECT if(timestamp >= toDateTime('{anchor}') - INTERVAL 24 HOUR, 'recent', 'earlier') AS w,
               round(avg(value), 3) AS avg_vib
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'WLD-01-UBD-RBT01' AND sensor_type = 'VIB'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 48 HOUR
        GROUP BY w
    """)
    half_map = {r["w"]: float(r["avg_vib"]) for r in halves}
    earlier = half_map.get("earlier", mean_v)
    recent = half_map.get("recent", mean_v)
    trend = "rising" if recent > earlier * 1.05 else "falling" if recent < earlier * 0.95 else "stable"
    status = "ABOVE" if max_v > 2.0 else "within"
    return [
        f"WLD-01-UBD-RBT01 vibration mean last 48h: {mean_v} {unit}",
        f"WLD-01-UBD-RBT01 vibration peak last 48h: {max_v} {unit}",
        f"Vibration trend (48h): {trend}",
        f"Peak is {status} safe limit of 2.0 mm/s per Fanuc specification",
    ]


def _gt_eq007() -> list[str]:
    """EQ-007: Fleet-wide machines at risk — lowest RUL and health index."""
    rows = _ch_query("""
        SELECT machine_id, component,
               round(health_index, 3) AS hi,
               round(rul_hours, 0)    AS rul
        FROM primeev_telemetry.degradation_state
        WHERE (machine_id, timestamp) IN (
            SELECT machine_id, max(timestamp) FROM primeev_telemetry.degradation_state GROUP BY machine_id
        )
        ORDER BY rul ASC
    """)
    if not rows:
        return []
    critical = [r for r in rows if float(r["rul"]) <= 0]
    high_risk = [r for r in rows if 0 < float(r["rul"]) <= 100]
    facts = []
    if critical:
        facts.append(f"{len(critical)} machine at RUL=0 (immediate risk): {', '.join(r['machine_id'] for r in critical)}")
    if high_risk:
        summary = ", ".join(f"{r['machine_id']}({int(float(r['rul']))}h)" for r in high_risk[:5])
        facts.append(f"{len(high_risk)} machines with RUL ≤100h: {summary}")
    lowest = min(rows, key=lambda r: float(r["hi"]))
    facts.append(f"Lowest health index: {lowest['machine_id']} hi={float(lowest['hi']):.3f} component={lowest['component']}")
    return facts


def _gt_eq008() -> list[str]:
    """EQ-008: MTTR by month for STP-01-PRS-HYP01 (last 6 months)."""
    rows = _ch_query("""
        SELECT formatDateTime(period_start, '%b') AS mon,
               round(mttr_hrs, 2) AS mttr,
               num_failures
        FROM primeev_telemetry.machine_reliability_metrics
        WHERE machine_id = 'STP-01-PRS-HYP01' AND period = 'monthly'
        ORDER BY period_start DESC LIMIT 6
    """)
    if not rows:
        return []
    return [
        f"STP-01-PRS-HYP01 {r['mon']}: MTTR={float(r['mttr'])}h ({r['num_failures']} failure(s))"
        for r in rows
    ]


def _gt_eq009() -> list[str]:
    """EQ-009: Spare parts inventory for hydraulic pump (SP-HYP-001 or compatible)."""
    rows = _pg_query("""
        SELECT part_number, description, quantity_on_hand, reorder_point, lead_time_days, location_bin
        FROM spare_parts_inventory
        WHERE part_number = 'SP-HYP-001'
    """)
    if not rows:
        rows = _pg_query("""
            SELECT part_number, description, quantity_on_hand, reorder_point, lead_time_days, location_bin
            FROM spare_parts_inventory
            WHERE compatible_machines::text LIKE '%STP-01-PRS-HYP01%'
            ORDER BY part_number LIMIT 1
        """)
    if not rows:
        return []
    r = rows[0]
    stock = "BELOW reorder point" if int(r["quantity_on_hand"]) <= int(r["reorder_point"]) else "adequate"
    return [
        f"{r['part_number']} ({r['description']}): qty={r['quantity_on_hand']}, reorder_point={r['reorder_point']}, lead_time={r['lead_time_days']}d",
        f"Stock status: {stock}, bin: {r['location_bin']}",
    ]


def _gt_eq010() -> list[str]:
    """EQ-010: Active vibration alerts — machines exceeding 2.0 mm/s threshold."""
    anchor = _ch_max_date("sensor_readings")
    rows = _ch_query(f"""
        SELECT machine_id,
               round(avg(value), 3) AS avg_vib,
               round(max(value), 3) AS peak_vib,
               any(unit) AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE sensor_type = 'VIB'
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 2 HOUR
        GROUP BY machine_id
        HAVING max(value) > 2.0
        ORDER BY peak_vib DESC
    """)
    if not rows:
        return ["No active vibration alerts — all machines within limits"]
    facts = []
    for r in rows:
        avg_v = round(float(r["avg_vib"]), 3)
        peak_v = round(float(r["peak_vib"]), 3)
        sev = "CRITICAL" if avg_v > 2.0 else "HIGH" if peak_v > 4.0 else "WARNING"
        facts.append(f"{r['machine_id']}: VIB {sev} — avg {avg_v} mm/s, peak {peak_v} mm/s (alarm limit 2.0 mm/s)")
    return facts


def _gt_eq012() -> list[str]:
    """EQ-012: Current hydraulic pressure and temperature at STP-01-PRS-HYP01."""
    anchor = _ch_max_date("sensor_readings")
    rows = _ch_query(f"""
        SELECT sensor_type,
               round(avg(value), 2) AS avg_val,
               round(max(value), 2) AS max_val,
               any(unit) AS unit
        FROM primeev_telemetry.sensor_readings
        WHERE machine_id = 'STP-01-PRS-HYP01'
          AND sensor_type IN ('PRS', 'TMP')
          AND timestamp >= toDateTime('{anchor}') - INTERVAL 1 HOUR
        GROUP BY sensor_type ORDER BY sensor_type
    """)
    if not rows:
        return []
    facts = []
    for r in rows:
        label = "hydraulic pressure" if r["sensor_type"] == "PRS" else "hydraulic oil temperature"
        unit = r["unit"] or ("bar" if r["sensor_type"] == "PRS" else "C")
        facts.append(f"STP-01-PRS-HYP01 {label} last 1h — avg: {float(r['avg_val'])} {unit}, max: {float(r['max_val'])} {unit}")
    return facts


def _gt_eq015() -> list[str]:
    """EQ-015: Last preventive maintenance for STP-01-PRS-HYP01."""
    rows = _pg_query("""
        SELECT type, DATE(started_at) AS maint_date, duration_min, parts_replaced
        FROM maintenance_history
        WHERE machine_id = 'STP-01-PRS-HYP01' AND type = 'preventive'
        ORDER BY started_at DESC LIMIT 1
    """)
    if not rows:
        return []
    r = rows[0]
    return [
        f"Last preventive maintenance: {r['maint_date']} (scheduled, duration {r['duration_min']} min)",
        f"Parts replaced: {r['parts_replaced']}",
    ]


# ── Production ─────────────────────────────────────────────────────────────

def _gt_pr003() -> list[str]:
    """PR-003: Last production day throughput by model."""
    anchor = _pg_max_date("production_batches", "end_time")
    rows = _pg_query(f"""
        SELECT vm.name AS model_name,
               SUM(pb.units_produced)::int AS produced,
               SUM(pb.units_passed)::int   AS passed
        FROM production_batches pb
        JOIN vehicle_models vm ON pb.model_id = vm.model_id
        WHERE DATE(pb.end_time) = '{anchor}'
        GROUP BY vm.name ORDER BY vm.name
    """)
    if not rows:
        return []
    total = sum(r["produced"] for r in rows)
    passed = sum(r["passed"] for r in rows)
    facts = [f"Last shift total ({anchor}): {total} vehicles produced, {passed} passed first inspection"]
    for r in rows:
        facts.append(f"{r['model_name']}: {r['produced']} produced, {r['passed']} passed")
    return facts


def _gt_pr004() -> list[str]:
    """PR-004: VIN trace for PEF-SD100-26-002000."""
    rows = _pg_query("""
        SELECT vr.vin_id, vm.name AS model_name,
               DATE(vr.production_date) AS prod_date, vr.status
        FROM vin_registry vr
        JOIN vehicle_models vm ON vr.model_id = vm.model_id
        WHERE vr.vin_id = 'PEF-SD100-26-002000'
    """)
    if not rows:
        return []
    v = rows[0]
    return [
        f"VIN PEF-SD100-26-002000: {v['model_name']}, production_date={v['prod_date']}, status={v['status']}",
    ]


def _gt_pr005() -> list[str]:
    """PR-005: BOM summary for PE-SV200."""
    rows = _pg_query("""
        SELECT COUNT(DISTINCT part_number) AS components,
               COUNT(DISTINCT station_id)  AS stations
        FROM bill_of_materials WHERE model_id = 'PE-SV200'
    """)
    if not rows:
        return []
    r = rows[0]
    return [f"PE-SV200 BOM: {r['components']} components across {r['stations']} stations"]


def _gt_pr006() -> list[str]:
    """PR-006: Raw material stock for PE-SD100 production run."""
    rows = _pg_query("""
        SELECT material_id, description, unit, quantity, reorder_point,
               CASE WHEN quantity <= 0 THEN 'CRITICAL'
                    WHEN quantity <= reorder_point THEN 'LOW'
                    ELSE 'OK' END AS status
        FROM raw_material_inventory
        ORDER BY status DESC, material_id
    """)
    if not rows:
        return []
    facts = [f"50 PE-SD100 units require raw materials — stock status:"]
    for r in rows[:8]:
        facts.append(f"  {r['material_id']} ({r['description']}): on_hand={r['quantity']} {r['unit']}, status={r['status']}")
    return facts


def _gt_pr007() -> list[str]:
    """PR-007: Assembly station cycle time targets from factory model."""
    try:
        from src.datagen.factory_model import FACTORY_STATIONS
        targets = {sid: FACTORY_STATIONS[sid].cycle_time_sec
                   for sid in ("ASM-01-PWR", "ASM-02-INT", "ASM-03-FNL")
                   if sid in FACTORY_STATIONS}
        if not targets:
            return []
        bottleneck = max(targets, key=targets.get)
        facts = [f"{sid}: ideal cycle time {t}s" for sid, t in sorted(targets.items())]
        facts.append(f"Bottleneck: {bottleneck} with highest ideal cycle time {targets[bottleneck]}s")
        return facts
    except Exception:
        return []


def _gt_pr008() -> list[str]:
    """PR-008: Raw materials below reorder point."""
    rows = _pg_query("""
        SELECT material_id, description, quantity, reorder_point,
               CASE WHEN quantity <= 0 THEN 'CRITICAL' ELSE 'LOW' END AS severity
        FROM raw_material_inventory
        WHERE quantity <= reorder_point
        ORDER BY quantity ASC
    """)
    if not rows:
        return ["All raw materials above reorder points"]
    facts = [f"{len(rows)} materials below reorder point:"]
    for r in rows:
        facts.append(f"  {r['material_id']} ({r['description']}): on_hand={r['quantity']}, reorder_point={r['reorder_point']} [{r['severity']}]")
    return facts


def _gt_pr010() -> list[str]:
    """PR-010: Daily production output — last 7 days from data anchor."""
    anchor = _pg_max_date("production_batches", "end_time")
    rows = _pg_query(f"""
        SELECT DATE(end_time) AS day,
               SUM(units_produced)::int AS produced,
               SUM(units_passed)::int   AS passed
        FROM production_batches
        WHERE end_time >= '{anchor}'::date - INTERVAL '7 days'
          AND end_time <= '{anchor}'::date + INTERVAL '1 day'
        GROUP BY DATE(end_time)
        ORDER BY day DESC LIMIT 7
    """)
    if not rows:
        return []
    total_avg = round(sum(r["produced"] for r in rows) / len(rows), 1)
    facts = [f"Daily output (last 7 days from {anchor}) — avg {total_avg} vehicles/day:"]
    for r in rows:
        facts.append(f"  {r['day']}: {r['produced']} produced, {r['passed']} passed")
    return facts


def _gt_pr011() -> list[str]:
    """PR-011: BOM for PE-SV200 + raw material inventory count."""
    bom = _pg_query("""
        SELECT COUNT(DISTINCT part_number) AS components,
               COUNT(DISTINCT station_id)  AS stations
        FROM bill_of_materials WHERE model_id = 'PE-SV200'
    """)
    inv = _pg_query("SELECT COUNT(*) AS n FROM raw_material_inventory")
    if not bom:
        return []
    b = bom[0]
    n = inv[0]["n"] if inv else 0
    return [f"PE-SV200 BOM: {b['components']} components, {n} raw materials directly tracked in inventory"]


# ── Quality ────────────────────────────────────────────────────────────────

def _gt_qa002() -> list[str]:
    """QA-002: SPC out-of-control signals at WLD-01-UBD."""
    rows = _ch_query("""
        SELECT parameter, out_of_control_signals, round(cpk, 3) AS cpk
        FROM primeev_telemetry.process_capability_history
        WHERE station_id = 'WLD-01-UBD' AND out_of_control_signals > 0
        ORDER BY timestamp DESC LIMIT 1 BY parameter
    """)
    if not rows:
        latest = _ch_query("""
            SELECT count() AS params_checked,
                   countIf(out_of_control_signals > 0) AS params_with_signals
            FROM primeev_telemetry.process_capability_history
            WHERE station_id = 'WLD-01-UBD'
              AND timestamp = (SELECT max(timestamp) FROM primeev_telemetry.process_capability_history
                               WHERE station_id = 'WLD-01-UBD')
        """)
        if latest and int(latest[0].get("params_with_signals") or 0) == 0:
            return ["WLD-01-UBD overall SPC status: in control — no active signals"]
        return []
    params = [r["parameter"] for r in rows]
    facts = [f"WLD-01-UBD overall status: OUT OF CONTROL — {len(params)} parameter(s) with active signals: {', '.join(params)}"]
    for r in rows:
        facts.append(f"  {r['parameter']}: Cpk={r['cpk']}, signals={r['out_of_control_signals']}")
    return facts


def _gt_qa003() -> list[str]:
    """QA-003: Sampling results for most recent STP-01-PRS lot."""
    rows = _pg_query("""
        SELECT insp_id, station_id, lot_number, lot_size, sample_size,
               aql_level, accept_number, reject_number, defects_found, disposition
        FROM sampling_inspections
        WHERE station_id = 'STP-01-PRS'
        ORDER BY timestamp DESC LIMIT 1
    """)
    if not rows:
        return []
    r = rows[0]
    result = "REJECT" if int(r["defects_found"]) > int(r["accept_number"]) else "ACCEPT"
    return [
        f"{r['lot_number']}: station={r['station_id']}, lot_size={r['lot_size']}, sample_size={r['sample_size']}, AQL={r['aql_level']}",
        f"accept_number={r['accept_number']}, defects_found={r['defects_found']} → {result}",
        f"Disposition: {r['disposition']}",
    ]


def _gt_qa004() -> list[str]:
    """QA-004: Defect rates at PNT-03-CLR — last 7 days relative to data anchor."""
    anchor = _pg_max_date("dimensional_inspections", "timestamp")
    rows = _pg_query(f"""
        SELECT COUNT(*)::int AS total,
               SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)::int AS failed,
               ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),1) AS defect_rate,
               ROUND(100.0*SUM(CASE WHEN result='pass' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),1) AS fpy
        FROM dimensional_inspections
        WHERE station_id = 'PNT-03-CLR'
          AND timestamp >= '{anchor}'::date - INTERVAL '7 days'
          AND timestamp <= '{anchor}'::date + INTERVAL '1 day'
    """)
    if not rows or not rows[0]["total"]:
        return []
    r = rows[0]
    top = _pg_query(f"""
        SELECT measurement_name, COUNT(*) AS n
        FROM dimensional_inspections
        WHERE station_id='PNT-03-CLR' AND result='fail'
          AND timestamp >= '{anchor}'::date - INTERVAL '7 days'
          AND timestamp <= '{anchor}'::date + INTERVAL '1 day'
        GROUP BY measurement_name ORDER BY n DESC LIMIT 4
    """)
    defect_str = ", ".join(f"{x['measurement_name']}({x['n']})" for x in top) if top else "n/a"
    return [
        f"PNT-03-CLR last 7 days (anchor {anchor}): {r['total']} inspections, {r['failed']} failed — defect rate {r['defect_rate']}%, FPY {r['fpy']}%",
        f"Top failing measurements: {defect_str}",
    ]


def _gt_qa005() -> list[str]:
    """QA-005: Rework history at Assembly stations — last 30 days."""
    rows = _pg_query("""
        SELECT COUNT(*)::int AS events,
               SUM(rework_time_min)::int AS total_min,
               ROUND(SUM(cost)::numeric, 2) AS total_cost
        FROM rework_records
        WHERE station_id IN ('ASM-01-PWR','ASM-02-INT','ASM-03-FNL')
          AND timestamp >= NOW() - INTERVAL '30 days'
    """)
    if not rows or not rows[0]["events"]:
        return []
    r = rows[0]
    return [f"Total Assembly rework last 30 days: {r['events']} events, {r['total_min']} min, ${r['total_cost']}"]


def _gt_qa006() -> list[str]:
    """QA-006: Supplier scorecard trend for SUP-MTL01 — last 6 months."""
    rows = _pg_query("""
        SELECT to_char(sc.month, 'Mon') AS mon,
               round(sc.defect_ppm::numeric, 1) AS ppm,
               round(sc.quality_score::numeric, 1) AS score
        FROM supplier_scorecards sc
        WHERE sc.supplier_id = 'SUP-MTL01'
        ORDER BY sc.month DESC LIMIT 6
    """)
    if not rows:
        return []
    score_trend = " → ".join(f"{r['mon']}={r['score']}" for r in reversed(rows))
    ppm_trend = " → ".join(str(r["ppm"]) for r in reversed(rows))
    latest_grade = "A" if float(rows[0]["score"]) >= 90 else "B" if float(rows[0]["score"]) >= 75 else "C" if float(rows[0]["score"]) >= 60 else "D"
    return [
        f"SUP-MTL01 quality score trend: {score_trend}",
        f"SUP-MTL01 defect PPM trend: {ppm_trend}",
        f"Latest grade: {latest_grade} (score={rows[0]['score']})",
    ]


def _gt_qa008() -> list[str]:
    """QA-008: Scrap records at Stamping stations — last 30 days."""
    rows = _pg_query("""
        SELECT COUNT(*)::int AS total_scraps,
               ROUND(SUM(cost)::numeric, 2) AS total_cost
        FROM scrap_records
        WHERE station_id IN ('STP-01-PRS','STP-02-PRS','STP-03-TRM')
          AND timestamp >= NOW() - INTERVAL '30 days'
    """)
    if not rows or not rows[0]["total_scraps"]:
        return []
    r = rows[0]
    return [f"Total Stamping scrap last 30 days: {r['total_scraps']} panels, ${r['total_cost']}"]


# ── Improvement ────────────────────────────────────────────────────────────

def _gt_im001() -> list[str]:
    """IM-001: WLD-01-UBD weld parameter change 2026-03-01 — before/after Cpk + defect rate."""
    cpk_b = _ch_query("""
        SELECT round(avg(cpk), 3) AS cpk FROM primeev_telemetry.process_capability_history
        WHERE station_id='WLD-01-UBD' AND parameter='nugget_diameter'
          AND timestamp >= '2026-01-30' AND timestamp < '2026-03-01'
    """)
    cpk_a = _ch_query("""
        SELECT round(avg(cpk), 3) AS cpk FROM primeev_telemetry.process_capability_history
        WHERE station_id='WLD-01-UBD' AND parameter='nugget_diameter'
          AND timestamp >= '2026-03-01' AND timestamp < '2026-04-01'
    """)
    dr_b = _pg_query("""
        SELECT ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dr
        FROM dimensional_inspections WHERE station_id='WLD-01-UBD'
          AND timestamp >= '2026-01-30' AND timestamp < '2026-03-01'
    """)
    dr_a = _pg_query("""
        SELECT ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dr
        FROM dimensional_inspections WHERE station_id='WLD-01-UBD'
          AND timestamp >= '2026-03-01' AND timestamp < '2026-04-01'
    """)
    facts = ["Change date: 2026-03-01 | Before: 2026-01-30–2026-02-28 | After: 2026-03-01–2026-03-31"]
    if cpk_b and cpk_b[0]["cpk"]:
        b = round(float(cpk_b[0]["cpk"]), 3)
        a = round(float(cpk_a[0]["cpk"]), 3) if cpk_a and cpk_a[0]["cpk"] else b
        facts.append(f"nugget_diameter Cpk before: {b} → after: {a} ({'improved' if a > b else 'declined'})")
    if dr_b and dr_b[0]["dr"]:
        b = round(float(dr_b[0]["dr"]), 2)
        a = round(float(dr_a[0]["dr"]), 2) if dr_a and dr_a[0]["dr"] else b
        facts.append(f"WLD-01-UBD defect rate before: {b}% → after: {a}%")
    return facts


def _gt_im002() -> list[str]:
    """IM-002: STP-01-PRS-HYP01 MTBF/MTTR before/after PM frequency change 2026-02-01."""
    before = _ch_query("""
        SELECT round(avg(mtbf_hrs), 1) AS mtbf, round(avg(mttr_hrs), 2) AS mttr,
               sum(num_failures) AS failures
        FROM primeev_telemetry.machine_reliability_metrics
        WHERE machine_id='STP-01-PRS-HYP01' AND period='monthly'
          AND period_start < '2026-02-01'
    """)
    after = _ch_query("""
        SELECT round(avg(mtbf_hrs), 1) AS mtbf, round(avg(mttr_hrs), 2) AS mttr,
               sum(num_failures) AS failures
        FROM primeev_telemetry.machine_reliability_metrics
        WHERE machine_id='STP-01-PRS-HYP01' AND period='monthly'
          AND period_start >= '2026-02-01'
    """)
    facts = ["Change date: 2026-02-01 | Before: Jan | After: Feb–Mar"]
    if before and before[0]["mtbf"]:
        b, a = before[0], (after[0] if after and after[0]["mtbf"] else before[0])
        facts.append(f"MTBF before: {float(b['mtbf'])}h → after: {float(a['mtbf'])}h")
        facts.append(f"MTTR before: {float(b['mttr'])}h → after: {float(a['mttr'])}h")
        facts.append(f"Failures before: {b['failures']} → after: {a['failures']}")
    return facts


def _gt_im003() -> list[str]:
    """IM-003: PNT-02-PRM defect/rework before/after paint booth upgrade 2026-03-01."""
    dr_b = _pg_query("""
        SELECT ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dr
        FROM dimensional_inspections WHERE station_id='PNT-02-PRM'
          AND timestamp >= '2026-01-30' AND timestamp < '2026-03-01'
    """)
    dr_a = _pg_query("""
        SELECT ROUND(100.0*SUM(CASE WHEN result='fail' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dr
        FROM dimensional_inspections WHERE station_id='PNT-02-PRM'
          AND timestamp >= '2026-03-01' AND timestamp < '2026-04-01'
    """)
    facts = ["Change date: 2026-03-01 | Before: Jan-30–Feb-28 | After: Mar-01–Mar-31"]
    if dr_b and dr_b[0]["dr"]:
        b = round(float(dr_b[0]["dr"]), 2)
        a = round(float(dr_a[0]["dr"]), 2) if dr_a and dr_a[0]["dr"] else b
        direction = "improved" if a < b else "worsened"
        facts.append(f"PNT-02-PRM defect rate before: {b}% → after: {a}% ({direction})")
    return facts


def _gt_im005() -> list[str]:
    """IM-005: WLD stage OEE comparison — Q1 vs Q2 2026."""
    before = _ch_query("""
        SELECT station_id,
               round(avg(oee)*100, 1) AS oee,
               round(avg(availability)*100, 1) AS avail,
               round(avg(performance)*100, 1) AS perf
        FROM primeev_telemetry.oee_metrics
        WHERE station_id IN ('WLD-01-UBD','WLD-02-SDP','WLD-03-RCL')
          AND timestamp >= '2026-01-01' AND timestamp < '2026-03-01'
        GROUP BY station_id ORDER BY station_id
    """)
    after = _ch_query("""
        SELECT station_id,
               round(avg(oee)*100, 1) AS oee,
               round(avg(availability)*100, 1) AS avail,
               round(avg(performance)*100, 1) AS perf
        FROM primeev_telemetry.oee_metrics
        WHERE station_id IN ('WLD-01-UBD','WLD-02-SDP','WLD-03-RCL')
          AND timestamp >= '2026-03-01'
        GROUP BY station_id ORDER BY station_id
    """)
    if not before or not after:
        return []
    after_map = {r["station_id"]: r for r in after}
    facts, best_delta, best_sid = [], None, None
    for b in before:
        sid = b["station_id"]
        a = after_map.get(sid, b)
        b_v = float(b["oee"])
        a_v = float(a["oee"])
        delta = round(a_v - b_v, 1)
        facts.append(f"{sid}: {b_v}% → {a_v}% (Δ{delta:+}pp) Avail Δ{round(float(a['avail'])-float(b['avail']),1):+}pp Perf Δ{round(float(a['perf'])-float(b['perf']),1):+}pp")
        if best_delta is None or delta > best_delta:
            best_delta, best_sid = delta, sid
    if best_sid:
        b_v = float(next(r["oee"] for r in before if r["station_id"] == best_sid))
        a_v = float(after_map[best_sid]["oee"])
        facts.insert(0, f"WLD improved most: {best_sid}: {b_v}% → {a_v}% ({best_delta:+}pp)")
    return facts


# ── Action ─────────────────────────────────────────────────────────────────

def _gt_ac003() -> list[str]:
    """AC-003: Receiving inspection for most recent SUP-MTL01 failed lot."""
    rows = _pg_query("""
        SELECT ri.lot_number, ri.result, ri.disposition,
               rm.part_number, rm.description,
               DATE(ri.inspection_date) AS insp_date
        FROM receiving_inspections ri
        JOIN raw_materials rm ON ri.material_id = rm.material_id
        WHERE ri.supplier_id = 'SUP-MTL01' AND ri.result = 'fail'
        ORDER BY ri.inspection_date DESC LIMIT 1
    """)
    if not rows:
        return []
    r = rows[0]
    return [
        f"Lot {r['lot_number']}: {r['part_number']} ({r['description']}), result={r['result']}, disposition={r['disposition']}",
        f"Inspection date: {r['insp_date']}",
    ]


# ── Robustness / Boundary ──────────────────────────────────────────────────

def _gt_bnd001() -> list[str]:
    """BND-001: WLD-01-UBD nugget_diameter Cpk — closest to 1.33 boundary."""
    rows = _ch_query("""
        SELECT toDate(timestamp) AS day, round(cpk, 3) AS cpk, round(cp, 3) AS cp
        FROM primeev_telemetry.process_capability_history
        WHERE station_id='WLD-01-UBD' AND parameter='nugget_diameter'
        ORDER BY ABS(cpk - 1.33) ASC, timestamp DESC LIMIT 1
    """)
    if not rows:
        return []
    cpk = round(float(rows[0]["cpk"]), 3)
    status = "capable" if cpk >= 1.33 else "marginal" if cpk >= 1.0 else "NOT CAPABLE"
    return [
        f"WLD-01-UBD nugget_diameter Cpk = {cpk} on {rows[0]['day']} — {status} (threshold 1.33)",
        f"Cp = {float(rows[0]['cp']):.3f}",
    ]


def _gt_bnd002() -> list[str]:
    """BND-002: STP-01-PRS surface_roughness Cpk — closest to 1.33 boundary."""
    rows = _ch_query("""
        SELECT toDate(timestamp) AS day, round(cpk, 3) AS cpk, round(cp, 3) AS cp
        FROM primeev_telemetry.process_capability_history
        WHERE station_id='STP-01-PRS' AND parameter='surface_roughness'
        ORDER BY ABS(cpk - 1.33) ASC, timestamp DESC LIMIT 1
    """)
    if not rows:
        return []
    cpk = round(float(rows[0]["cpk"]), 3)
    status = "capable" if cpk >= 1.33 else "marginal" if cpk >= 1.0 else "NOT CAPABLE"
    return [
        f"STP-01-PRS surface_roughness Cpk = {cpk} on {rows[0]['day']} — {status} (threshold 1.33)",
        f"Cp = {float(rows[0]['cp']):.3f}",
    ]


def _gt_bnd003() -> list[str]:
    """BND-003: PNT-03-CLR OEE record nearest 75% target."""
    rows = _ch_query("""
        SELECT toDate(timestamp) AS day, shift,
               round(oee*100, 2) AS oee_pct,
               round(availability*100, 2) AS avail_pct,
               round(performance*100, 2)  AS perf_pct,
               round(quality*100, 2)      AS qual_pct
        FROM primeev_telemetry.oee_metrics
        WHERE station_id='PNT-03-CLR'
        ORDER BY ABS(oee - 0.75) ASC, timestamp DESC LIMIT 1
    """)
    if not rows:
        return []
    r = rows[0]
    rel = "at" if abs(float(r["oee_pct"]) - 75.0) < 0.1 else ("above" if float(r["oee_pct"]) >= 75 else "just below")
    return [
        f"PNT-03-CLR OEE = {r['oee_pct']}% on {r['day']} {r['shift']} shift "
        f"(Availability={r['avail_pct']}%, Performance={r['perf_pct']}%, Quality={r['qual_pct']}%) — {rel} 75% target",
    ]


def _gt_bnd004() -> list[str]:
    """BND-004: ASM-01-PWR OEE record nearest 75% target."""
    rows = _ch_query("""
        SELECT toDate(timestamp) AS day, shift,
               round(oee*100, 2) AS oee_pct,
               round(availability*100, 2) AS avail_pct,
               round(performance*100, 2)  AS perf_pct,
               round(quality*100, 2)      AS qual_pct
        FROM primeev_telemetry.oee_metrics
        WHERE station_id='ASM-01-PWR'
        ORDER BY ABS(oee - 0.75) ASC, timestamp DESC LIMIT 1
    """)
    if not rows:
        return []
    r = rows[0]
    rel = "at target" if abs(float(r["oee_pct"]) - 75.0) < 0.1 else ("above" if float(r["oee_pct"]) >= 75 else "just below target")
    return [
        f"ASM-01-PWR OEE = {r['oee_pct']}% on {r['day']} {r['shift']} shift "
        f"(Availability={r['avail_pct']}%, Performance={r['perf_pct']}%, Quality={r['qual_pct']}%) — {rel}",
    ]


def _gt_bnd005() -> list[str]:
    """BND-005: Receiving inspection with conditional disposition for SUP-MTL01."""
    rows = _pg_query("""
        SELECT ri.lot_number, ri.result, ri.disposition,
               rm.part_number, rm.description
        FROM receiving_inspections ri
        JOIN raw_materials rm ON ri.material_id = rm.material_id
        WHERE ri.supplier_id='SUP-MTL01' AND ri.disposition='conditional'
        ORDER BY ri.inspection_date DESC LIMIT 1
    """)
    if not rows:
        return []
    r = rows[0]
    return [
        f"{r['lot_number']}: result={r['result']}, disposition={r['disposition']} — SteelWorks Inc. ({r['part_number']})",
        "Conditional disposition requires engineering sign-off before use in production",
    ]


def _gt_bnd006() -> list[str]:
    """BND-006: AQL boundary — eval query embeds the scenario; GT confirms the correct AQL decision.

    The eval query states: INS-SMP-099999, defects_found=1, accept_number=1 → agent must decide.
    AQL rule: defects_found ≤ accept_number → ACCEPT. This is a reasoning test, not a DB lookup.
    """
    return [
        "AQL boundary rule: defects_found ≤ accept_number → ACCEPT (ties are not a reject)",
        "INS-SMP-099999 scenario: defects_found=1, accept_number=1 → ACCEPT per AQL standard",
    ]


def _gt_cd001() -> list[str]:
    """CD-001: PNT-03-CLR OEE — Jan 2026 vs Mar 2026 comparison."""
    jan = _ch_query("SELECT round(avg(oee)*100, 2) AS oee FROM primeev_telemetry.oee_metrics WHERE station_id='PNT-03-CLR' AND toYYYYMM(timestamp)=202601")
    mar = _ch_query("SELECT round(avg(oee)*100, 2) AS oee FROM primeev_telemetry.oee_metrics WHERE station_id='PNT-03-CLR' AND toYYYYMM(timestamp)=202603")
    if not jan or not mar:
        return []
    j = round(float(jan[0]["oee"]), 2)
    m = round(float(mar[0]["oee"]), 2)
    delta = round(m - j, 2)
    return [f"PNT-03-CLR OEE Jan 2026: {j}% → Mar 2026: {m}% — {'decline' if delta < 0 else 'improvement'} of {abs(delta):.2f}pp"]


def _gt_cd002() -> list[str]:
    """CD-002: WLD-01-UBD Cpk + total rework — complex diagnosis case."""
    cpk = _ch_query("""
        SELECT toDate(timestamp) AS day, round(cpk, 3) AS cpk
        FROM primeev_telemetry.process_capability_history
        WHERE station_id='WLD-01-UBD' AND parameter='nugget_diameter'
        ORDER BY ABS(cpk - 1.33) ASC LIMIT 1
    """)
    rw = _pg_query("""
        SELECT COUNT(*)::int AS count, ROUND(SUM(cost)::numeric, 2) AS cost
        FROM rework_records WHERE station_id='WLD-01-UBD'
    """)
    facts = []
    if cpk:
        v = round(float(cpk[0]["cpk"]), 3)
        status = "capable" if v >= 1.33 else "marginal"
        facts.append(f"WLD-01-UBD nugget_diameter Cpk: {v} on {cpk[0]['day']} — {status} (threshold 1.33)")
    if rw and rw[0]["count"]:
        facts.append(f"WLD-01-UBD total reworks: {rw[0]['count']}, total cost ${rw[0]['cost']}")
    return facts


def _gt_cd003() -> list[str]:
    """CD-003: SUP-MTL01 supplier scorecard trend."""
    rows = _pg_query("""
        SELECT to_char(month, 'Mon') AS mon,
               round(quality_score::numeric, 1) AS score,
               round(defect_ppm::numeric, 1) AS ppm
        FROM supplier_scorecards
        WHERE supplier_id='SUP-MTL01'
        ORDER BY month DESC LIMIT 6
    """)
    if not rows:
        return []
    score_trend = " → ".join(f"{r['mon']}={r['score']}" for r in reversed(rows))
    ppm_trend = " → ".join(str(r["ppm"]) for r in reversed(rows))
    return [
        f"SteelWorks (SUP-MTL01) quality score trend: {score_trend}",
        f"Defect PPM trend: {ppm_trend}",
    ]


def _gt_cd004() -> list[str]:
    """CD-004: Full VIN trace for PEF-SD100-26-002000 — complex diagnosis."""
    return _gt_pr004()  # same query, reuse


def _gt_con003() -> list[str]:
    """CON-003: Preventive maintenance history for STP-01-PRS-HYP01 — parts consistency check."""
    rows = _pg_query("""
        SELECT DATE(started_at) AS maint_date, duration_min, parts_replaced
        FROM maintenance_history
        WHERE machine_id='STP-01-PRS-HYP01' AND type='preventive'
        ORDER BY started_at DESC LIMIT 3
    """)
    if not rows:
        return []
    facts = [f"Last {len(rows)} preventive PMs for STP-01-PRS-HYP01:"]
    for r in rows:
        facts.append(f"  {r['maint_date']}: duration={r['duration_min']}min, parts={r['parts_replaced']}")
    return facts


def _gt_mt001() -> list[str]:
    """MT-001: WLD station OEE in January 2026 — multi-turn context data."""
    rows = _ch_query("""
        SELECT station_id,
               round(avg(oee)*100, 2)          AS oee_pct,
               round(avg(availability)*100, 2)  AS avail_pct,
               round(avg(performance)*100, 2)   AS perf_pct,
               round(avg(quality)*100, 2)       AS qual_pct
        FROM primeev_telemetry.oee_metrics
        WHERE station_id IN ('WLD-01-UBD','WLD-02-SDP','WLD-03-RCL')
          AND toYYYYMM(timestamp)=202601
        GROUP BY station_id ORDER BY station_id
    """)
    if not rows:
        return []
    return [
        f"{r['station_id']} Jan: OEE={r['oee_pct']}%, Avail={r['avail_pct']}%, Perf={r['perf_pct']}%, Qual={r['qual_pct']}%"
        for r in rows
    ]


def _gt_mt002() -> list[str]:
    """MT-002: Machine context fact carried forward from multi-turn turn 1."""
    return ["Machine: STP-01-PRS-HYP01 — carried from turn 1"]


def _gt_mt003() -> list[str]:
    """MT-003: Station context fact carried forward from multi-turn turn 1."""
    return ["Station: WLD-01-UBD — carried from turn 1"]


def _gt_mt004() -> list[str]:
    """MT-004: Supplier context fact carried forward from multi-turn turn 1."""
    return ["Supplier: SUP-MTL01 (SteelWorks Inc.) — carried from turn 1"]


# ── Registry: case_id → query function ─────────────────────────────────────

GT_REGISTRY: dict[str, Callable[[], list[str]]] = {
    # Equipment
    "EQ-001": _gt_eq001,
    "EQ-002": _gt_eq002,
    "EQ-003": _gt_eq003,
    "EQ-004": _gt_eq004,
    "EQ-005": _gt_eq005,
    "EQ-006": _gt_eq006,
    "EQ-007": _gt_eq007,
    "EQ-008": _gt_eq008,
    "EQ-009": _gt_eq009,
    "EQ-010": _gt_eq010,
    "EQ-012": _gt_eq012,
    "EQ-014": _gt_eq014,
    "EQ-015": _gt_eq015,
    # EQ-011: search_sop RAG-only — SOP content not in DB
    # EQ-013: search_equipment_manual RAG-only
    # Production
    "PR-001": _gt_pr001,
    "PR-002": _gt_pr002,
    "PR-003": _gt_pr003,
    "PR-004": _gt_pr004,
    "PR-005": _gt_pr005,
    "PR-006": _gt_pr006,
    "PR-007": _gt_pr007,
    "PR-008": _gt_pr008,
    "PR-010": _gt_pr010,
    "PR-011": _gt_pr011,
    # PR-009: search_sop RAG-only
    # Quality
    "QA-001": _gt_qa001,
    "QA-002": _gt_qa002,
    "QA-003": _gt_qa003,
    "QA-004": _gt_qa004,
    "QA-005": _gt_qa005,
    "QA-006": _gt_qa006,
    "QA-008": _gt_qa008,
    "QA-009": _gt_qa009,
    # QA-007: search_fmea_risks RAG-only
    # Improvement
    "IM-001": _gt_im001,
    "IM-002": _gt_im002,
    "IM-003": _gt_im003,
    "IM-005": _gt_im005,
    "IM-006": _gt_im006,
    # IM-004: search_case_study RAG-only
    # Action
    "AC-003": _gt_ac003,
    "AC-009": _gt_ac009,
    # AC-001,002,004,005,006: document format assertions — no DB values
    # Robustness — boundary
    "BND-001": _gt_bnd001,
    "BND-002": _gt_bnd002,
    "BND-003": _gt_bnd003,
    "BND-004": _gt_bnd004,
    "BND-005": _gt_bnd005,
    "BND-006": _gt_bnd006,
    # Robustness — complex diagnosis
    "CD-001": _gt_cd001,
    "CD-002": _gt_cd002,
    "CD-003": _gt_cd003,
    "CD-004": _gt_cd004,
    # Robustness — constraint / multi-turn
    "CON-003": _gt_con003,
    "MT-001":  _gt_mt001,
    "MT-002":  _gt_mt002,
    "MT-003":  _gt_mt003,
    "MT-004":  _gt_mt004,
    # CL-*, NF-*, RT-*, SF-*, CON-001/002: behavioral/RAG assertions — no DB data
}


# ── Core generator logic ────────────────────────────────────────────────────

def populate_case(case: dict, dry_run: bool = False) -> tuple[bool, str]:
    """Populate key_facts.data for a single eval case.

    Returns:
        (changed: bool, message: str)
    """
    case_id = case.get("id", "")
    if case_id not in GT_REGISTRY:
        return False, f"{case_id}: no GT query registered - skipping"

    try:
        data_facts = GT_REGISTRY[case_id]()
    except Exception as e:
        return False, f"{case_id}: DB query failed - {e}"

    if not data_facts:
        return False, f"{case_id}: query returned no rows - DB may need seeding"

    # key_facts lives under ground_truth; ensure the dict exists
    gt = case.setdefault("ground_truth", {})
    existing = gt.get("key_facts", {})

    # Migrate flat list format → {domain, data} dict if needed
    if isinstance(existing, list):
        gt["key_facts"] = {"domain": existing, "data": data_facts}
    elif isinstance(existing, dict):
        existing["data"] = data_facts
    else:
        gt["key_facts"] = {"domain": [], "data": data_facts}

    if dry_run:
        preview = "\n    ".join(data_facts)
        return True, f"{case_id}: would write {len(data_facts)} data facts:\n    {preview}"

    return True, f"{case_id}: populated {len(data_facts)} data facts"


def run(target_case: str | None = None, dry_run: bool = False) -> None:
    """Main entry point — iterate all eval case files and populate GT."""
    json_files = sorted(EVAL_DIR.rglob("*.json"))
    total_changed = 0
    total_skipped = 0

    for json_file in json_files:
        with open(json_file) as f:
            cases = json.load(f)

        file_changed = False
        for case in cases:
            if target_case and case.get("id") != target_case:
                continue
            changed, msg = populate_case(case, dry_run=dry_run)
            print(f"  {'OK' if changed else '--'} {msg}")
            if changed:
                file_changed = True
                total_changed += 1
            else:
                total_skipped += 1

        if file_changed and not dry_run:
            with open(json_file, "w") as f:
                json.dump(cases, f, indent=2)
            print(f"  >> wrote {json_file.name}")

    print(f"\nDone: {total_changed} cases updated, {total_skipped} skipped.")
    if dry_run:
        print("(dry run - no files written)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate eval case key_facts.data from DB")
    parser.add_argument("--case", help="Only process this specific case ID (e.g. PR-001)")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing files")
    args = parser.parse_args()

    print(f"Ground truth generator - {'DRY RUN ' if args.dry_run else ''}scanning {EVAL_DIR}\n")
    try:
        run(target_case=args.case, dry_run=args.dry_run)
    except Exception as e:
        print(f"\nFailed: {e}")
        print("Make sure Postgres and ClickHouse are running (docker compose up).")
        sys.exit(1)
