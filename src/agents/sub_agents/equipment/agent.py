"""Equipment Agent — diagnose failures, predict degradation, recommend maintenance."""

from google.adk.agents import Agent

from src.agents.model import get_agent_model
from src.agents.prompts.equipment import EQUIPMENT_SYSTEM_PROMPT
from src.agents.tools.energy_tools import get_energy_consumption, get_energy_trend
from src.agents.tools.failure_tools import (
    get_active_alerts,
    get_failure_by_id,
    get_failure_history,
)
from src.agents.tools.inventory_tools import get_spare_parts
from src.agents.tools.maintenance_tools import (
    create_work_order,
    get_maintenance_history,
    get_work_orders,
)
from src.agents.tools.rag_tools import (
    search_equipment_manual,
    search_past_issues,
    search_sop,
)
from src.agents.tools.reliability_tools import (
    get_degradation_status,
    get_failure_rate_trend,
    get_mtbf_mttr,
    get_reliability_report,
)
from src.agents.tools.sensor_tools import (
    fetch_sensor_data,
    get_current_readings,
    get_sensor_trend,
)

equipment_agent = Agent(
    name="equipment_agent",
    model=get_agent_model(),
    description=(
        "Equipment specialist — handles machine failures, sensor diagnostics, "
        "predictive maintenance, MTBF/MTTR analysis, energy monitoring, and spare parts. "
        "Route here for any question about machines, sensors, maintenance, or equipment health."
    ),
    instruction=EQUIPMENT_SYSTEM_PROMPT,
    tools=[
        fetch_sensor_data,
        get_sensor_trend,
        get_current_readings,
        get_failure_history,
        get_active_alerts,
        get_failure_by_id,
        get_maintenance_history,
        get_work_orders,
        create_work_order,
        get_mtbf_mttr,
        get_reliability_report,
        get_degradation_status,
        get_failure_rate_trend,
        get_energy_consumption,
        get_energy_trend,
        get_spare_parts,
        search_sop,
        search_equipment_manual,
        search_past_issues,
    ],
)

