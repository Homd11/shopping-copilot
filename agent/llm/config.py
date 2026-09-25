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
    provider: Literal["scripted", "nvidia", "groq", "bedrock"]
    model: str
    api_key: SecretStr | None = None
    endpoint: str | None = None
    timeout_seconds: float = 20
    stream: bool = False
    reasoning_effort: str | None = None


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
    if provider not in {"scripted", "nvidia", "groq", "bedrock"}:
        raise LLMConfigurationError(f"Unsupported LLM_PROVIDER: {provider}")
    api_key_name = "GROQ_API_KEY" if provider == "groq" else "NVIDIA_API_KEY"
    api_key_text = values.get(api_key_name, "").strip()
    if provider == "nvidia" and not api_key_text:
        raise LLMConfigurationError("NVIDIA_API_KEY is required for the nvidia provider")
    if provider == "groq" and not api_key_text:
        raise LLMConfigurationError("GROQ_API_KEY is required for the groq provider")
    endpoint = None
    timeout_seconds = 20.0
    stream = False
    reasoning_effort = None
    if provider == "nvidia":
        endpoint = values.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()
        if not endpoint:
            raise LLMConfigurationError("NVIDIA_BASE_URL must not be empty")
        try:
            timeout_seconds = float(values.get("LLM_TIMEOUT_SECONDS", "20"))
        except ValueError as error:
            raise LLMConfigurationError("LLM_TIMEOUT_SECONDS must be a number") from error
        if timeout_seconds <= 0:
            raise LLMConfigurationError("LLM_TIMEOUT_SECONDS must be positive")
        stream_text = values.get("NVIDIA_STREAM", "false").strip().lower()
        if stream_text not in {"true", "false"}:
            raise LLMConfigurationError("NVIDIA_STREAM must be true or false")
        stream = stream_text == "true"
    if provider == "groq":
        endpoint = values.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        if not endpoint:
            raise LLMConfigurationError("GROQ_BASE_URL must not be empty")
        try:
            timeout_seconds = float(values.get("LLM_TIMEOUT_SECONDS", "20"))
        except ValueError as error:
            raise LLMConfigurationError("LLM_TIMEOUT_SECONDS must be a number") from error
        if timeout_seconds <= 0:
            raise LLMConfigurationError("LLM_TIMEOUT_SECONDS must be positive")
        reasoning_effort = values.get("LLM_REASONING_EFFORT", "none").strip().lower()
        if reasoning_effort not in {"none", "low", "medium", "high"}:
            raise LLMConfigurationError("LLM_REASONING_EFFORT must be none, low, medium, or high")
    return LLMSettings(
        provider=provider,
        model=model,
        api_key=SecretStr(api_key_text) if api_key_text else None,
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
        stream=stream,
        reasoning_effort=reasoning_effort,
    )
