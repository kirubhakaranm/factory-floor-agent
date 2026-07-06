"""Improvement (PDCA) Agent â€” before/after analysis, continuous improvement."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.agents.prompts.improvement import IMPROVEMENT_SYSTEM_PROMPT
from src.agents.tools.comparison_tools import compare_periods, compare_shifts
from src.agents.tools.production_tools import get_cycle_times, get_oee_metrics, get_throughput
from src.agents.tools.quality_tools import get_defect_rates, get_rework_history
from src.agents.tools.rag_tools import search_case_study, search_fmea_risks, search_past_issues
from src.agents.tools.reliability_tools import get_mtbf_mttr
from src.agents.tools.spc_tools import get_cpk, get_process_capability

improvement_agent = Agent(
    name="improvement_agent",
    model=LiteLlm(model="anthropic/claude-sonnet-5"),
    description=(
        "Continuous improvement specialist â€” handles PDCA analysis, before/after comparisons, "
        "Six Sigma metrics, FMEA updates, and improvement effectiveness validation. "
        "Route here when the user wants to evaluate whether a change improved results."
    ),
    instruction=IMPROVEMENT_SYSTEM_PROMPT,
    tools=[
        get_cpk,
        get_process_capability,
        get_defect_rates,
        get_rework_history,
        get_oee_metrics,
        get_cycle_times,
        get_throughput,
        get_mtbf_mttr,
        compare_periods,
        compare_shifts,
        search_fmea_risks,
        search_case_study,
        search_past_issues,
    ],
)
