"""Analytics endpoints — OEE by stage, failure pareto, Cpk summary, reliability."""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

_STAGE_MAP = {
    "STP": "Stamping",
    "WLD": "Welding",
    "PNT": "Paint",
    "ASM": "Assembly",
    "QAT": "Quality",
}


@router.get("/oee")
async def get_oee_by_stage() -> dict:
    """Latest OEE averaged per stage using the most recent snapshot from ClickHouse."""
    loop = asyncio.get_event_loop()
    try:
        from src.db.clickhouse import queries as ch
        rows = await loop.run_in_executor(None, ch.get_all_stations_latest_oee)
    except Exception:
        rows = []

    stage_buckets: dict[str, list] = {code: [] for code in _STAGE_MAP}
    for row in rows:
        code = str(row.get("station_id", ""))[:3]
        if code in stage_buckets:
            stage_buckets[code].append(row)

    stages = []
    for code, name in _STAGE_MAP.items():
        bucket = stage_buckets[code]
        if bucket:
            def _avg(key: str) -> float:
                """Average a numeric field across all rows in the stage bucket."""
                return round(sum(float(r.get(key, 0)) for r in bucket) / len(bucket), 3)
            stages.append({
                "stage_code": code,
                "stage_name": name,
                "oee": _avg("latest_oee"),
                "availability": _avg("latest_availability"),
                "performance": _avg("latest_performance"),
                "quality": _avg("latest_quality"),
                "station_count": len(bucket),
            })
        else:
            stages.append({
                "stage_code": code, "stage_name": name,
                "oee": 0.0, "availability": 0.0, "performance": 0.0, "quality": 0.0,
                "station_count": 0,
            })

    return {"stages": stages, "as_of": datetime.now(timezone.utc).isoformat()}


@router.get("/failures")
async def get_failure_pareto(days_back: int = 30) -> dict:
    """Top failure modes by count over the given time window (Postgres equipment_failures)."""
    loop = asyncio.get_event_loop()
    try:
        from src.db.postgres import queries as pg
        failures = await loop.run_in_executor(
            None, pg.sync_get_recent_failures, None, None, days_back, 500
        )
    except Exception:
        failures = []

    mode_counts: dict[str, int] = {}
    for f in failures:
        mode = f.get("failure_mode") or "Unknown"
        mode_counts[mode] = mode_counts.get(mode, 0) + 1

    total = sum(mode_counts.values()) or 1
    top = sorted(mode_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    return {
        "failure_modes": [
            {"mode": mode, "count": count, "pct": round(count / total * 100, 1)}
            for mode, count in top
        ],
        "total": sum(mode_counts.values()),
        "days_back": days_back,
    }


@router.get("/cpk")
async def get_cpk_summary() -> dict:
    """Latest Cpk per (station_id, parameter) from process_capability_history."""
    loop = asyncio.get_event_loop()
    try:
        from src.db.clickhouse import queries as ch
        rows = await loop.run_in_executor(None, ch.get_latest_cpk_all)
    except Exception:
        rows = []

    return {
        "entries": [
            {
                "station_id": r.get("station_id", ""),
                "parameter": r.get("parameter", ""),
                "cpk": round(float(r.get("cpk", 0)), 3),
                "cp": round(float(r.get("cp", 0)), 3),
                "out_of_control_signals": int(r.get("out_of_control_signals", 0)),
                "trending_alert": bool(r.get("trending_alert", 0)),
            }
            for r in rows
        ]
    }


@router.get("/reliability")
async def get_reliability_summary() -> dict:
    """MTBF and MTTR per station computed from equipment failures (last 30 days)."""
    loop = asyncio.get_event_loop()
    try:
        from src.db.postgres import queries as pg
        failures = await loop.run_in_executor(
            None, pg.sync_get_recent_failures, None, None, 30, 500
        )
    except Exception:
        failures = []

    WINDOW_HRS = 30 * 24
    station_failures: dict[str, list] = {}
    for f in failures:
        sid = f.get("station_id", "")
        if sid:
            station_failures.setdefault(sid, []).append(f)

    stations = []
    for sid in sorted(station_failures):
        recs = station_failures[sid]
        count = len(recs)
        avg_downtime_min = sum(r.get("downtime_min") or 0 for r in recs) / count
        mtbf = round(WINDOW_HRS / count, 1)
        mttr = round(avg_downtime_min / 60, 2)
        avail = round(mtbf / (mtbf + mttr) * 100, 1) if (mtbf + mttr) > 0 else 100.0
        stations.append({
            "station_id": sid,
            "failure_count": count,
            "mtbf_hrs": mtbf,
            "mttr_hrs": mttr,
            "availability_pct": avail,
        })

    return {"stations": stations, "days_back": 30}
