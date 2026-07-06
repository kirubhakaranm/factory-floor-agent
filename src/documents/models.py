"""Document output data models — structured data for PDF rendering."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    EIGHT_D = "8d_report"
    NCR = "ncr_report"
    WORK_ORDER = "work_order"
    INCIDENT_REPORT = "incident_report"
    PDCA_RECORD = "pdca_record"
    MAINTENANCE_NOTICE = "maintenance_notice"


@dataclass
class DocumentMeta:
    doc_id: str
    doc_type: DocumentType
    title: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "Factory Floor Agent"
    revision: str = "1.0"
    status: str = "Draft"
    pdf_path: str | None = None


@dataclass
class EightDReport:
    meta: DocumentMeta
    d1_team: list[str]
    d2_problem: str
    d3_containment: str
    d4_root_cause: str
    d5_corrective_actions: str
    d6_verification: str = "Monitoring for 30 days post-implementation"
    d7_preventive_actions: str = ""
    d8_closure: str = "Pending effectiveness verification"
    related_failure_id: str | None = None
    related_station_id: str | None = None
    affected_models: list[str] = field(default_factory=list)
    units_affected: int = 0
    cost_impact: float = 0.0


@dataclass
class NcrReport:
    meta: DocumentMeta
    supplier_id: str
    supplier_name: str
    lot_id: str
    material_description: str
    nonconformance: str
    quantity_affected: int = 0
    disposition: str = "return"
    supplier_response_due: str = "10 business days"
    receiving_inspection_ref: str | None = None
    quality_impact: str = ""
    photos_attached: bool = False


@dataclass
class WorkOrderDoc:
    meta: DocumentMeta
    machine_id: str
    machine_model: str
    station_id: str
    wo_type: str  # preventive, corrective, predictive
    priority: str  # critical, high, medium, low
    description: str
    tasks: list[str] = field(default_factory=list)
    parts_required: list[dict] = field(default_factory=list)
    estimated_duration_min: int = 60
    assigned_to: str = "Next available technician"
    safety_requirements: list[str] = field(default_factory=list)
    related_failure_id: str | None = None


@dataclass
class IncidentReport:
    meta: DocumentMeta
    incident_type: str  # equipment_failure, quality_event, safety
    station_id: str
    machine_id: str | None = None
    severity: str = "major"
    timeline: list[dict] = field(default_factory=list)
    root_cause: str = ""
    immediate_actions: str = ""
    corrective_actions: str = ""
    preventive_actions: str = ""
    units_affected: int = 0
    downtime_min: int = 0
    cost_total: float = 0.0
    distribution: list[str] = field(default_factory=list)


@dataclass
class PdcaRecord:
    meta: DocumentMeta
    problem: str
    plan_description: str
    plan_hypothesis: str
    plan_metrics: list[str] = field(default_factory=list)
    do_action: str = ""
    do_date: str = ""
    check_before: dict = field(default_factory=dict)
    check_after: dict = field(default_factory=dict)
    check_change_pct: dict = field(default_factory=dict)
    check_statistical_confidence: str = "moderate"
    check_side_effects: str = "None detected"
    act_decision: str = ""  # standardize, modify, revert
    act_rationale: str = ""
    act_next_steps: list[str] = field(default_factory=list)
    fmea_reference: str | None = None
    follow_up_date: str | None = None


@dataclass
class MaintenanceNotice:
    meta: DocumentMeta
    machine_id: str
    machine_model: str
    station_id: str
    maintenance_type: str
    scheduled_date: str
    estimated_duration: str
    production_impact: str
    tasks_summary: str
    parts_pre_staged: bool = False
    shift_affected: str = ""
    supervisor_notified: bool = False
    alternate_routing: str = ""
