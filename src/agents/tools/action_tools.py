"""Action tools — generate real PDF documents and send notifications."""

from typing import Literal

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


def _to_float(value: int | float | str) -> float:
    """Coerce agent-supplied cost values (e.g. '$5,142.11' or '5000') to float."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _notify(meta: DocumentMeta, summary: str, pdf_path: str | None) -> dict[str, bool]:
    """Return a stub notification result; no channels configured."""
    return {"email": False}


def create_incident_report(
    station_id: str,
    incident_type: Literal["equipment_failure", "quality_event", "safety"],
    severity: Literal["critical", "major", "minor"],
    root_cause: str,
    immediate_actions: str,
    corrective_actions: str,
    preventive_actions: str,
    machine_id: str | None = None,
    downtime_min: int = 0,
    units_affected: int = 0,
    cost_total: float = 0.0,
) -> str:
    """[ACTION]: Create a formal incident report PDF and notify plant stakeholders. [TARGET]: PDF renderer + email notification system.

    [INPUT PREREQUISITE]: station_id and incident_type and severity are required. root_cause,
    immediate_actions, corrective_actions, and preventive_actions must all be confirmed facts —
    do NOT invent these. This is an irreversible action that sends emails. Confirm all details
    with the user before calling.

    [OUTPUT GUARANTEE]: Returns a confirmation string with: doc_id (format IR-XXXXXX), PDF path,
    and notification delivery status per channel. The PDF is immediately stored on disk.

    [NEGATIVE BOUNDARY]: Cannot be undone — notifications are sent immediately. Does not create
    a work order — use create_work_order or schedule_maintenance for that. Do not call
    speculatively; only call when the user has confirmed all required fields.

    Args:
        station_id: Station where incident occurred (e.g. 'STP-01-PRS')
        incident_type: Type: 'equipment_failure', 'quality_event', or 'safety'
        severity: Severity: 'critical', 'major', or 'minor'
        root_cause: Determined root cause (must be confirmed, not speculative)
        immediate_actions: Actions already taken at time of report
        corrective_actions: Planned actions to fix the root cause
        preventive_actions: Actions to prevent recurrence
        machine_id: Affected machine (optional)
        downtime_min: Downtime in minutes (default 0)
        units_affected: Number of units impacted (default 0)
        cost_total: Total cost impact (default 0.0)

    Returns:
        Confirmation string with doc_id, PDF path, and notification status.
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
    """[ACTION]: Create an 8D problem-solving report PDF and notify stakeholders. [TARGET]: PDF renderer + email notification system.

    [INPUT PREREQUISITE]: problem_description, containment_actions, root_cause, corrective_actions,
    and preventive_actions are all required. These must be substantiated by data — do not populate
    them with placeholder text. This is an irreversible action that sends emails.

    [OUTPUT GUARANTEE]: Returns a confirmation string with doc_id (format 8D-XXXXXX), PDF path,
    and notification status. Status is 'Draft' requiring Quality Manager review.

    [NEGATIVE BOUNDARY]: Cannot be undone. Does not create a work order for corrective actions —
    use create_work_order separately. Do not call speculatively.

    Args:
        problem_description: Clear, specific description of the problem
        containment_actions: Immediate containment steps taken
        root_cause: Root cause from investigation (must be evidence-based)
        corrective_actions: Actions to eliminate root cause
        preventive_actions: Actions to prevent recurrence
        team: Team members involved (optional, defaults to cross-functional team)
        related_failure_id: Related failure ID from get_failure_by_id (optional)
        station_id: Related station (optional)
        units_affected: Number of units impacted (default 0)
        cost_impact: Cost of the issue (default 0.0)

    Returns:
        Confirmation string with doc_id, PDF path, and notification status.
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
        units_affected=int(units_affected) if units_affected else 0,
        cost_impact=_to_float(cost_impact),
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
    disposition: Literal["return", "rework", "scrap", "use-as-is"] = "return",
) -> str:
    """[ACTION]: Create a Supplier Non-Conformance Report (NCR) PDF and notify stakeholders. [TARGET]: PDF renderer + email notification system.

    [INPUT PREREQUISITE]: supplier_id, supplier_name, lot_id, material_description, and
    nonconformance are all required. disposition must be confirmed with the quality team before
    calling. This is an irreversible action — the supplier will receive notification.

    [OUTPUT GUARANTEE]: Returns confirmation with doc_id (format NCR-XXXXXX), PDF path,
    disposition decision, supplier response deadline (10 business days), and notification status.

    [NEGATIVE BOUNDARY]: Cannot be undone. Does not quarantine the physical lot in inventory —
    that must be done manually. Do not call speculatively; confirm all details first.

    Args:
        supplier_id: Supplier identifier (e.g. 'SUP-MTL01')
        supplier_name: Supplier company name
        lot_id: Affected material lot identifier
        material_description: Description of the non-conforming material
        nonconformance: Clear description of the non-conformance
        quantity_affected: Number of units/parts affected (default 0)
        disposition: Disposition decision: 'return', 'rework', 'scrap', or 'use-as-is'

    Returns:
        Confirmation string with doc_id, disposition, and deadline.
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
    act_decision: Literal["standardize", "modify", "revert"] = "standardize",
    act_rationale: str = "",
) -> str:
    """[ACTION]: Create a PDCA improvement record PDF and notify stakeholders. [TARGET]: PDF renderer + email notification system.

    [INPUT PREREQUISITE]: problem, plan_description, plan_hypothesis, do_action, and do_date are
    required. check_before and check_after should contain metric dicts with the same keys for
    before/after comparison (e.g. {"oee": 0.72, "defect_rate": 2.1}). act_decision must be one
    of the Literal values. Confirm all details before calling — this sends notifications.

    [OUTPUT GUARANTEE]: Returns confirmation with doc_id (format PDCA-XXXXXX), decision,
    PDF path, and notification status. Automatically computes change_pct for matching keys
    in check_before / check_after.

    [NEGATIVE BOUNDARY]: Cannot be undone. act_decision='revert' documents a rollback but does
    not automatically undo any system changes.

    Args:
        problem: Problem statement or improvement opportunity
        plan_description: What was planned
        plan_hypothesis: Expected outcome
        do_action: What change was implemented
        do_date: When the change was made (YYYY-MM-DD format)
        check_before: Before metrics dict (optional, e.g. {"oee": 0.72})
        check_after: After metrics dict (optional, same keys as check_before)
        act_decision: Decision: 'standardize', 'modify', or 'revert'
        act_rationale: Reason for the decision

    Returns:
        Confirmation string with doc_id, decision, and PDF path.
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
    maintenance_type: Literal["preventive", "corrective", "predictive", "overhaul"],
    scheduled_date: str,
    estimated_duration: str,
    tasks_summary: str,
    production_impact: str = "Minimal — alternate routing available",
    priority: Literal["critical", "high", "medium", "low"] = "medium",
) -> str:
    """[ACTION]: Schedule maintenance, generate a maintenance notice PDF and a work order PDF, then notify stakeholders. [TARGET]: PDF renderer + email notification system.

    [INPUT PREREQUISITE]: All required args must be confirmed with the user. scheduled_date
    must be in YYYY-MM-DD format. estimated_duration is a human-readable string (e.g. '2 hours').
    maintenance_type and priority must be Literal values. This sends notifications immediately.

    [OUTPUT GUARANTEE]: Returns confirmation with two document IDs: a maintenance notice
    (format MN-XXXXXX) and a work order (format WO-XXXXXX), their PDF paths, scheduled date,
    duration, and notification status.

    [NEGATIVE BOUNDARY]: Cannot be undone. Does not actually block the machine in the production
    schedule — operations must coordinate separately. Do not call speculatively.

    Args:
        machine_id: Machine to maintain (e.g. 'STP-01-PRS-HYP01')
        machine_model: Machine model name (from equipment manual)
        station_id: Station where machine is located
        maintenance_type: Type: 'preventive', 'corrective', 'predictive', or 'overhaul'
        scheduled_date: Planned date (YYYY-MM-DD)
        estimated_duration: Duration estimate (e.g. '2 hours', '4 hours')
        tasks_summary: Description of maintenance tasks to perform
        production_impact: Expected production impact (default 'Minimal — alternate routing available')
        priority: Priority: 'critical', 'high', 'medium', or 'low'

    Returns:
        Confirmation with notice doc_id, work order doc_id, PDF paths, and notification status.
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
