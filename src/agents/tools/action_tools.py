"""Action tools — generate real PDF documents and send notifications."""

from datetime import datetime

from src.documents.models import (
    DocumentMeta,
    DocumentType,
    EightDReport,
    IncidentReport,
    MaintenanceNotice,
    NcrReport,
    PdcaRecord,
    WorkOrderDoc,
)
from src.documents.renderer import generate_doc_id, render_pdf
from src.notifications.channels.email_smtp import EmailChannel
from src.notifications.router import NotificationRouter

_router = NotificationRouter()
_router.register_channel(EmailChannel())


def _notify(meta: DocumentMeta, summary: str, pdf_path) -> dict[str, bool]:
    """Send notification through all configured channels."""
    from pathlib import Path
    return _router.notify(meta, summary, Path(pdf_path) if pdf_path else None)


def create_incident_report(
    station_id: str,
    incident_type: str,
    severity: str,
    root_cause: str,
    immediate_actions: str,
    corrective_actions: str,
    preventive_actions: str,
    machine_id: str | None = None,
    downtime_min: int = 0,
    units_affected: int = 0,
    cost_total: float = 0.0,
) -> str:
    """Create a formal incident report as PDF and notify stakeholders.

    Args:
        station_id: Station where incident occurred
        incident_type: Type: equipment_failure, quality_event, safety
        severity: Severity: critical, major, minor
        root_cause: Determined root cause
        immediate_actions: Actions already taken
        corrective_actions: Actions to fix the root cause
        preventive_actions: Actions to prevent recurrence
        machine_id: Affected machine (optional)
        downtime_min: Downtime in minutes
        units_affected: Number of units impacted
        cost_total: Total cost impact

    Returns:
        Confirmation with document ID and PDF path
    """
    doc_id = generate_doc_id(DocumentType.INCIDENT_REPORT)
    meta = DocumentMeta(
        doc_id=doc_id,
        doc_type=DocumentType.INCIDENT_REPORT,
        title=f"Incident at {station_id} — {incident_type.replace('_', ' ').title()}",
        status="Issued",
    )
    doc = IncidentReport(
        meta=meta,
        incident_type=incident_type,
        station_id=station_id,
        machine_id=machine_id,
        severity=severity,
        root_cause=root_cause,
        immediate_actions=immediate_actions,
        corrective_actions=corrective_actions,
        preventive_actions=preventive_actions,
        downtime_min=downtime_min,
        units_affected=units_affected,
        cost_total=cost_total,
        distribution=["Plant Manager", "Quality Manager", "Maintenance Manager"],
    )

    pdf_path = render_pdf(DocumentType.INCIDENT_REPORT, meta, doc)
    notifications = _notify(meta, f"Incident report {doc_id} issued for {station_id}: {root_cause[:100]}", pdf_path)

    return (
        f"Incident Report created: {doc_id}\n"
        f"PDF: {pdf_path}\n"
        f"Notifications: {notifications}"
    )


def create_8d_report(
    problem_description: str,
    containment_actions: str,
    root_cause: str,
    corrective_actions: str,
    preventive_actions: str,
    team: list[str] | None = None,
    related_failure_id: str | None = None,
    station_id: str | None = None,
    units_affected: int = 0,
    cost_impact: float = 0.0,
) -> str:
    """Create an 8D problem-solving report as PDF and notify stakeholders.

    Args:
        problem_description: Clear description of the problem
        containment_actions: Immediate containment
        root_cause: Root cause from investigation
        corrective_actions: Actions to eliminate root cause
        preventive_actions: Actions to prevent recurrence
        team: Team members involved (optional)
        related_failure_id: Related failure ID (optional)
        station_id: Related station (optional)
        units_affected: Number of units impacted
        cost_impact: Cost of the issue

    Returns:
        Confirmation with document ID and PDF path
    """
    doc_id = generate_doc_id(DocumentType.EIGHT_D)
    meta = DocumentMeta(
        doc_id=doc_id,
        doc_type=DocumentType.EIGHT_D,
        title=f"8D: {problem_description[:80]}",
        status="Draft",
    )
    doc = EightDReport(
        meta=meta,
        d1_team=team or ["Quality Engineering", "Process Engineering", "Maintenance"],
        d2_problem=problem_description,
        d3_containment=containment_actions,
        d4_root_cause=root_cause,
        d5_corrective_actions=corrective_actions,
        d7_preventive_actions=preventive_actions,
        related_failure_id=related_failure_id,
        related_station_id=station_id,
        units_affected=units_affected,
        cost_impact=cost_impact,
    )

    pdf_path = render_pdf(DocumentType.EIGHT_D, meta, doc)
    notifications = _notify(meta, f"8D Report {doc_id} created: {problem_description[:100]}", pdf_path)

    return (
        f"8D Report created: {doc_id}\n"
        f"PDF: {pdf_path}\n"
        f"Status: Draft — requires Quality Manager review\n"
        f"Notifications: {notifications}"
    )


def create_supplier_ncr(
    supplier_id: str,
    supplier_name: str,
    lot_id: str,
    material_description: str,
    nonconformance: str,
    quantity_affected: int = 0,
    disposition: str = "return",
) -> str:
    """Create a Supplier Non-Conformance Report (NCR) as PDF and notify stakeholders.

    Args:
        supplier_id: Supplier identifier (e.g., 'SUP-MTL01')
        supplier_name: Supplier company name
        lot_id: Affected material lot
        material_description: Description of the material
        nonconformance: Description of the non-conformance
        quantity_affected: Number of units/parts affected
        disposition: Action: return, rework, scrap, use-as-is

    Returns:
        Confirmation with document ID and PDF path
    """
    doc_id = generate_doc_id(DocumentType.NCR)
    meta = DocumentMeta(
        doc_id=doc_id,
        doc_type=DocumentType.NCR,
        title=f"NCR: {supplier_name} — {lot_id}",
        status="Issued",
    )
    doc = NcrReport(
        meta=meta,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        lot_id=lot_id,
        material_description=material_description,
        nonconformance=nonconformance,
        quantity_affected=quantity_affected,
        disposition=disposition,
    )

    pdf_path = render_pdf(DocumentType.NCR, meta, doc)
    notifications = _notify(meta, f"NCR {doc_id} issued against {supplier_name} for lot {lot_id}: {nonconformance[:100]}", pdf_path)

    return (
        f"Supplier NCR created: {doc_id}\n"
        f"PDF: {pdf_path}\n"
        f"Disposition: {disposition}\n"
        f"Supplier response due: 10 business days\n"
        f"Notifications: {notifications}"
    )


def create_pdca_record(
    problem: str,
    plan_description: str,
    plan_hypothesis: str,
    do_action: str,
    do_date: str,
    check_before: dict | None = None,
    check_after: dict | None = None,
    act_decision: str = "standardize",
    act_rationale: str = "",
) -> str:
    """Create a PDCA improvement record as PDF and notify stakeholders.

    Args:
        problem: Problem or improvement opportunity
        plan_description: What was planned
        plan_hypothesis: Expected outcome
        do_action: What change was implemented
        do_date: When the change was made
        check_before: Before metrics dict (optional)
        check_after: After metrics dict (optional)
        act_decision: Decision: standardize, modify, revert
        act_rationale: Reason for decision

    Returns:
        Confirmation with document ID and PDF path
    """
    doc_id = generate_doc_id(DocumentType.PDCA_RECORD)
    meta = DocumentMeta(
        doc_id=doc_id,
        doc_type=DocumentType.PDCA_RECORD,
        title=f"PDCA: {problem[:80]}",
        status="Completed",
    )

    check_before = check_before or {}
    check_after = check_after or {}
    change_pct = {}
    for key in check_before:
        if key in check_after:
            try:
                before_val = float(check_before[key])
                after_val = float(check_after[key])
                if before_val != 0:
                    pct = ((after_val - before_val) / before_val) * 100
                    change_pct[key] = f"{pct:+.1f}%"
            except (ValueError, TypeError):
                change_pct[key] = "N/A"

    doc = PdcaRecord(
        meta=meta,
        problem=problem,
        plan_description=plan_description,
        plan_hypothesis=plan_hypothesis,
        do_action=do_action,
        do_date=do_date,
        check_before=check_before,
        check_after=check_after,
        check_change_pct=change_pct,
        act_decision=act_decision,
        act_rationale=act_rationale,
    )

    pdf_path = render_pdf(DocumentType.PDCA_RECORD, meta, doc)
    notifications = _notify(meta, f"PDCA Record {doc_id}: {act_decision.upper()} — {problem[:100]}", pdf_path)

    return (
        f"PDCA Record created: {doc_id}\n"
        f"Decision: {act_decision.upper()}\n"
        f"PDF: {pdf_path}\n"
        f"Notifications: {notifications}"
    )


def schedule_maintenance(
    machine_id: str,
    machine_model: str,
    station_id: str,
    maintenance_type: str,
    scheduled_date: str,
    estimated_duration: str,
    tasks_summary: str,
    production_impact: str = "Minimal — alternate routing available",
    priority: str = "medium",
) -> str:
    """Schedule maintenance and generate a maintenance notification PDF.

    Args:
        machine_id: Machine identifier
        machine_model: Machine model name
        station_id: Station identifier
        maintenance_type: Type: preventive, corrective, predictive, overhaul
        scheduled_date: Planned date (YYYY-MM-DD)
        estimated_duration: Duration estimate (e.g., '2 hours')
        tasks_summary: Summary of maintenance tasks
        production_impact: Expected impact on production
        priority: Priority: critical, high, medium, low

    Returns:
        Confirmation with document ID and PDF path
    """
    doc_id = generate_doc_id(DocumentType.MAINTENANCE_NOTICE)
    meta = DocumentMeta(
        doc_id=doc_id,
        doc_type=DocumentType.MAINTENANCE_NOTICE,
        title=f"Maintenance: {machine_id} — {maintenance_type.title()}",
        status="Scheduled",
    )
    doc = MaintenanceNotice(
        meta=meta,
        machine_id=machine_id,
        machine_model=machine_model,
        station_id=station_id,
        maintenance_type=maintenance_type,
        scheduled_date=scheduled_date,
        estimated_duration=estimated_duration,
        production_impact=production_impact,
        tasks_summary=tasks_summary,
    )

    pdf_path = render_pdf(DocumentType.MAINTENANCE_NOTICE, meta, doc)
    notifications = _notify(meta, f"Maintenance scheduled: {machine_id} on {scheduled_date} ({estimated_duration})", pdf_path)

    # Also create a work order
    wo_doc_id = generate_doc_id(DocumentType.WORK_ORDER)
    wo_meta = DocumentMeta(
        doc_id=wo_doc_id,
        doc_type=DocumentType.WORK_ORDER,
        title=f"WO: {machine_id} — {maintenance_type.title()} Maintenance",
        status="Scheduled",
    )
    wo_doc = WorkOrderDoc(
        meta=wo_meta,
        machine_id=machine_id,
        machine_model=machine_model,
        station_id=station_id,
        wo_type=maintenance_type,
        priority=priority,
        description=tasks_summary,
    )
    wo_path = render_pdf(DocumentType.WORK_ORDER, wo_meta, wo_doc)

    return (
        f"Maintenance scheduled:\n"
        f"  Notification: {doc_id} -> {pdf_path}\n"
        f"  Work Order: {wo_doc_id} -> {wo_path}\n"
        f"  Date: {scheduled_date} | Duration: {estimated_duration}\n"
        f"  Notifications: {notifications}"
    )
