"""Action Agent â€” generate work orders, incident reports, 8D, NCRs, PDCA records."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.agents.prompts.action import ACTION_SYSTEM_PROMPT
from src.agents.tools.action_tools import (
    create_8d_report,
    create_incident_report,
    create_pdca_record,
    create_supplier_ncr,
    schedule_maintenance,
)
from src.agents.tools.maintenance_tools import create_work_order
from src.agents.tools.rag_tools import search_past_issues, search_sop

action_agent = Agent(
    name="action_agent",
    model=LiteLlm(model="anthropic/claude-sonnet-5"),
    description=(
        "Documentation and action specialist â€” generates work orders, incident reports, "
        "8D problem-solving reports, supplier NCRs, PDCA records, and maintenance schedules. "
        "Route here when the user wants to create a document or take an action."
    ),
    instruction=ACTION_SYSTEM_PROMPT,
    tools=[
        create_work_order,
        create_incident_report,
        create_8d_report,
        create_supplier_ncr,
        create_pdca_record,
        schedule_maintenance,
        search_sop,
        search_past_issues,
    ],
)
