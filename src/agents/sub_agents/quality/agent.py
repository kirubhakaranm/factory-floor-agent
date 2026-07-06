"""Quality Agent â€” inspections, SPC, Cpk, AQL, rework, supplier quality."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.agents.prompts.quality import QUALITY_SYSTEM_PROMPT
from src.agents.tools.quality_tools import (
    get_defect_rates,
    get_dimensional_results,
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
    get_receiving_inspections,
    get_supplier_ncrs,
    get_supplier_scorecard,
)

quality_agent = Agent(
    name="quality_agent",
    model=LiteLlm(model="anthropic/claude-sonnet-5"),
    description=(
        "Quality specialist â€” handles inspections (dimensional, visual, sampling/AQL), "
        "SPC monitoring, Cpk/process capability, defect analysis, rework/scrap tracking, "
        "supplier quality, and FMEA. Route here for any quality-related question."
    ),
    instruction=QUALITY_SYSTEM_PROMPT,
    tools=[
        get_dimensional_results,
        get_sampling_results,
        get_visual_checklist,
        get_defect_rates,
        get_rework_history,
        get_spc_data,
        get_cpk,
        get_process_capability,
        check_control_rules,
        get_receiving_inspections,
        get_supplier_scorecard,
        get_supplier_ncrs,
        search_specification,
        search_past_issues,
        search_fmea_risks,
        search_sop,
    ],
)
