from collections.abc import Mapping
from dataclasses import dataclass
from os import environ
from typing import Literal

from dotenv import load_dotenv
from pydantic import SecretStr


class LLMConfigurationError(ValueError):
    """The selected model provider cannot start with the supplied configuration."""


@dataclass(frozen=True)
class LLMSettings:
    provider: Literal["scripted", "nvidia", "bedrock"]
    model: str
    api_key: SecretStr | None = None


def load_llm_settings(environment: Mapping[str, str] | None = None) -> LLMSettings:
    if environment is None:
        load_dotenv()
    values = environ if environment is None else environment
    provider = values.get("LLM_PROVIDER", "").strip()
    if not provider:
        raise LLMConfigurationError("LLM_PROVIDER is required")
    model = values.get("LLM_MODEL", "").strip()
    if not model:
        raise LLMConfigurationError("LLM_MODEL is required")
    if provider not in {"scripted", "nvidia", "bedrock"}:
        raise LLMConfigurationError(f"Unsupported LLM_PROVIDER: {provider}")
    api_key_text = values.get("NVIDIA_API_KEY", "").strip()
    if provider == "nvidia" and not api_key_text:
        raise LLMConfigurationError("NVIDIA_API_KEY is required for the nvidia provider")
    return LLMSettings(
        provider=provider,
        model=model,
        api_key=SecretStr(api_key_text) if api_key_text else None,
    )
