"""Root agent â€” PrimeEV Factory Floor Assistant. Routes to domain specialists."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.agents.prompts.root import ROOT_SYSTEM_PROMPT
from src.agents.sub_agents.action.agent import action_agent
from src.agents.sub_agents.equipment.agent import equipment_agent
from src.agents.sub_agents.improvement.agent import improvement_agent
from src.agents.sub_agents.production.agent import production_agent
from src.agents.sub_agents.quality.agent import quality_agent

root_agent = Agent(
    name="primeev_factory_agent",
    model=LiteLlm(model="anthropic/claude-sonnet-5"),
    description="PrimeEV Motors Factory Floor AI Assistant â€” routes to domain specialists",
    instruction=ROOT_SYSTEM_PROMPT,
    sub_agents=[
        equipment_agent,
        quality_agent,
        production_agent,
        improvement_agent,
        action_agent,
    ],
)
