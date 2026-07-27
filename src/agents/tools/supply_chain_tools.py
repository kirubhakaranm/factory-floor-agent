"""Supply chain tools — receiving inspections, supplier scorecards, NCRs,
and component consumption for lot traceability."""

from typing import Literal

from src.db.postgres import queries as pg


def get_receiving_inspections(
    supplier_id: str | None = None,
    result_filter: Literal["pass", "fail", "conditional"] | None = None,
    limit: int = 20,
) -> list[dict]:
    """[ACTION]: Retrieve receiving inspection records for incoming materials. [TARGET]: receiving_inspections table (Postgres).

    [INPUT PREREQUISITE]: All filters are optional. supplier_id format: 'SUP-MTL01', 'SUP-ELC02', etc.
    result_filter must be a Literal value if provided.

    [OUTPUT GUARANTEE]: Returns inspection rows with: ri_id, material_id, supplier_id, lot_number,
    inspection_date, result (pass/fail/conditional), disposition (accept/reject/conditional),
    first_article_status. Ordered by inspection_date descending.

    [NEGATIVE BOUNDARY]: Cannot return supplier scorecard metrics — use get_supplier_scorecard.
    Cannot return NCRs — use get_supplier_ncrs. Cannot filter by material type or date range.

    Args:
        supplier_id: Filter by supplier (optional, e.g. 'SUP-MTL01')
        result_filter: Filter by result: 'pass', 'fail', or 'conditional' (optional)
        limit: Maximum results (default 20)

    Returns:
        List of receiving inspection dicts.
    """
    return pg.sync_get_receiving_inspections(supplier_id, result_filter, limit)


def get_supplier_scorecard(supplier_id: str) -> list[dict] | str:
    """[ACTION]: Retrieve monthly supplier performance scorecard for the last 12 months. [TARGET]: supplier_scorecards table (Postgres), joined with suppliers.

    [INPUT PREREQUISITE]: supplier_id must be a valid supplier code (e.g. 'SUP-MTL01').

    [OUTPUT GUARANTEE]: Returns monthly rows with: supplier_name, supplier_id, month,
    defect_ppm, on_time_pct, quality_score (0–100), lot_count, grade (A/B/C/D).
    Grade: A ≥ 90, B ≥ 75, C ≥ 60, D < 60. Ordered newest-first.

    [NEGATIVE BOUNDARY]: Cannot return scorecard for multiple suppliers in one call.
    Cannot return individual lot-level data — use get_receiving_inspections for that.

    Args:
        supplier_id: Supplier identifier (e.g. 'SUP-MTL01')

    Returns:
        Monthly scorecard list. TERMINAL string if supplier not found.
    """
    data = pg.sync_get_supplier_scorecard(supplier_id)
    if not data:
        return (
            f"TERMINAL: No scorecard data found for supplier '{supplier_id}'. "
            "Valid format: SUP-MTL01, SUP-ELC02, etc. Do not retry."
        )
    return data


def get_supplier_ncrs(
    supplier_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """[ACTION]: Retrieve supplier non-conformance reports (NCRs). [TARGET]: supplier_ncrs table (Postgres).

    [INPUT PREREQUISITE]: supplier_id is optional. Without it, returns the most recent NCRs factory-wide.

    [OUTPUT GUARANTEE]: Returns NCR rows with: ncr_id, supplier_id, lot_id, issue, disposition, date.
    Ordered by date descending. Empty list means no NCRs on record.

    [NEGATIVE BOUNDARY]: Cannot create new NCRs — use create_supplier_ncr in action_tools.
    Cannot return full NCR text — only structured fields.

    Args:
        supplier_id: Filter by supplier (optional)
        limit: Maximum results (default 20)

    Returns:
        List of NCR dicts.
    """
    return pg.sync_get_supplier_ncrs(supplier_id, limit)


def get_component_consumption(
    batch_id: str | None = None,
    lot_number: str | None = None,
    part_number: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """[ACTION]: Trace which production batches consumed a specific lot or component — core lot traceability tool. [TARGET]: component_consumption table (Postgres).

    [INPUT PREREQUISITE]: Provide at least one filter for meaningful results. Given a suspect
    lot_number from a receiving inspection failure, this finds every batch that consumed it.
    Cross-reference batch_id results with vin_registry to identify affected vehicles.

    [OUTPUT GUARANTEE]: Returns consumption rows with: batch_id, consumed_date, station_id,
    part_number, model_id, lot_number, qty_consumed. Empty list means no records match —
    the lot may not have been consumed yet or the identifier is incorrect.

    [NEGATIVE BOUNDARY]: Cannot return downstream VIN-level impact directly — join with
    vin_registry after getting results. Cannot trace beyond first-tier supplier lots.

    Args:
        batch_id: Filter by production batch (e.g. 'B-000042') — optional
        lot_number: Filter by supplier lot number (e.g. 'LOT-STP-2601-0023') — optional
        part_number: Filter by component part number (e.g. 'CHS-SD100-001') — optional
        limit: Maximum results (default 50)

    Returns:
        List of component consumption rows.
    """
    return pg.sync_get_component_consumption(batch_id, lot_number, part_number, limit)
