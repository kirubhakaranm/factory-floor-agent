"""Central model factory — returns a LiteLlm instance from settings.

Set AGENT_MODEL in .env to switch providers without touching agent code:
  AGENT_MODEL=anthropic/claude-haiku-4-5          # default (Anthropic API)
  AGENT_MODEL=ollama/qwen2.5:14b                  # local Ollama
  AGENT_MODEL=ollama/llama3.1:8b                  # local Ollama (lighter)
"""

from google.adk.models.lite_llm import LiteLlm
from src.config.settings import settings


def get_agent_model() -> LiteLlm:
    """Construct a LiteLlm instance from the configured AGENT_MODEL setting."""
    model_str = settings.agent_model
    kwargs: dict = {"model": model_str}
    if model_str.startswith("ollama/"):
        kwargs["api_base"] = settings.ollama_base_url
    return LiteLlm(**kwargs)
