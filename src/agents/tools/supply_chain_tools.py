"""Supply chain tools — receiving inspections, supplier scorecards, NCRs."""


def get_receiving_inspections(
    supplier_id: str | None = None,
    result_filter: str | None = None,
    limit: int = 20,
) -> str:
    """Get receiving inspection records for incoming materials.

    Args:
        supplier_id: Filter by supplier (optional)
        result_filter: Filter by result: pass, fail, conditional (optional)
        limit: Maximum results

    Returns:
        Inspection records with material, supplier, lot_number, result, disposition
    """
    filters = []
    if supplier_id:
        filters.append(f"supplier={supplier_id}")
    if result_filter:
        filters.append(f"result={result_filter}")
    return (
        f"Querying receiving inspections ({', '.join(filters) or 'all'}, limit: {limit}). "
        "Returns ri_id, material_id, supplier_id, lot_number, result, disposition, first_article_status."
    )


def get_supplier_scorecard(supplier_id: str) -> str:
    """Get monthly supplier performance scorecard.

    Args:
        supplier_id: Supplier identifier (e.g., 'SUP-MTL01')

    Returns:
        Monthly scores: defect_ppm, on_time_pct, quality_score, delivery_score, overall_grade
    """
    return (
        f"Querying scorecard for {supplier_id}. Returns monthly: "
        "defect_ppm, on_time_pct, quality_score, delivery_score, overall_grade (A/B/C/D)."
    )


def get_supplier_ncrs(
    supplier_id: str | None = None,
    limit: int = 20,
) -> str:
    """Get supplier non-conformance reports (NCRs).

    Args:
        supplier_id: Filter by supplier (optional)
        limit: Maximum results

    Returns:
        NCR records with issue description, disposition (return/rework/scrap/use-as-is)
    """
    return (
        f"Querying supplier NCRs (supplier: {supplier_id or 'all'}, limit: {limit}). "
        "Returns ncr_id, supplier_id, lot_id, issue, disposition, date."
    )
