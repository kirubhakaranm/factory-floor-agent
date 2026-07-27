"""Production Agent — OEE, throughput, BOM, inventory, VIN tracing, shift comparisons."""

from google.adk.agents import Agent

from src.agents.model import get_agent_model
from src.agents.prompts.production import PRODUCTION_SYSTEM_PROMPT
from src.agents.tools.bom_tools import check_mrp, get_bom_for_model, get_component_usage
from src.agents.tools.comparison_tools import (
    compare_periods,
    compare_shifts,
    compare_stations,
)
from src.agents.tools.inventory_tools import (
    get_consumables_level,
    get_inventory_transaction_history,
    get_raw_material_stock,
    get_spare_parts,
    get_wip_status,
)
from src.agents.tools.production_tools import (
    get_batch_status,
    get_cycle_times,
    get_oee_metrics,
    get_throughput,
)
from src.agents.tools.rag_tools import search_sop, search_specification
from src.agents.tools.supply_chain_tools import get_component_consumption
from src.agents.tools.vin_tools import get_vin_quality_summary, trace_vin_history

production_agent = Agent(
    name="production_agent",
    model=get_agent_model(),
    description=(
        "Production specialist — handles OEE, throughput, cycle times, batch status, "
        "Bill of Materials, MRP, VIN traceability, inventory levels, and shift/period/station comparisons. "
        "Route here for production performance, scheduling, and logistics questions."
    ),
    instruction=PRODUCTION_SYSTEM_PROMPT,
    tools=[
        get_oee_metrics,
        get_batch_status,
        get_cycle_times,
        get_throughput,
        get_bom_for_model,
        get_component_usage,
        check_mrp,
        trace_vin_history,
        get_vin_quality_summary,
        get_raw_material_stock,
        get_consumables_level,
        get_wip_status,
        get_spare_parts,
        get_inventory_transaction_history,
        get_component_consumption,
        compare_shifts,
        compare_periods,
        compare_stations,
        search_sop,
        search_specification,
    ],
)

