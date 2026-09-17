from agent.llm.config import LLMConfigurationError, LLMSettings
from agent.llm.contract import LLMClient, ScriptedLLMClient


def build_llm_client(settings: LLMSettings) -> LLMClient:
    if settings.provider == "scripted":
        return ScriptedLLMClient()
    raise LLMConfigurationError(
        f"The {settings.provider} LLM adapter is not available in this build"
    )
