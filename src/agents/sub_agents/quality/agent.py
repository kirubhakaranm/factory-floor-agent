"""Quality Agent — inspections, SPC, Cpk, AQL, rework, supplier quality."""

from google.adk.agents import Agent

from src.agents.model import get_agent_model
from src.agents.prompts.quality import QUALITY_SYSTEM_PROMPT
from src.agents.tools.quality_tools import (
    get_aql_recommendation,
    get_defect_catalog,
    get_defect_rates,
    get_dimensional_results,
    get_inspection_plan,
    get_measurement_specs,
    get_rework_history,
    get_sampling_results,
    get_visual_checklist,
)
from src.agents.tools.rag_tools import (
    search_fmea_risks,
    search_past_issues,
    search_specification,
    search_sop,
)
from src.agents.tools.spc_tools import (
    check_control_rules,
    get_cpk,
    get_process_capability,
    get_spc_data,
)
from src.agents.tools.supply_chain_tools import (
    get_component_consumption,
    get_receiving_inspections,
    get_supplier_ncrs,
    get_supplier_scorecard,
)

quality_agent = Agent(
    name="quality_agent",
    model=get_agent_model(),
    description=(
        "Quality specialist — handles inspections (dimensional, visual, sampling/AQL), "
        "SPC monitoring, Cpk/process capability, defect analysis, rework/scrap tracking, "
        "supplier quality, and FMEA. Route here for any quality-related question."
    ),
    instruction=QUALITY_SYSTEM_PROMPT,
    tools=[
        # Inspection results
        get_dimensional_results,
        get_sampling_results,
        get_visual_checklist,
        get_defect_rates,
        get_rework_history,
        # Quality master data
        get_defect_catalog,
        get_inspection_plan,
        get_aql_recommendation,
        get_measurement_specs,
        # SPC / capability
        get_spc_data,
        get_cpk,
        get_process_capability,
        check_control_rules,
        # Supply chain / traceability
        get_receiving_inspections,
        get_supplier_scorecard,
        get_supplier_ncrs,
        get_component_consumption,
        # RAG
        search_specification,
        search_past_issues,
        search_fmea_risks,
        search_sop,
    ],
)

