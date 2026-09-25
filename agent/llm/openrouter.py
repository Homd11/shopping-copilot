"""Bounded paid Gemini evaluation through OpenRouter, with no automatic retries."""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from math import isfinite
from time import monotonic

import httpx

from agent.llm.config import LLMConfigurationError, LLMSettings
from agent.llm.contract import LLMChunk, LLMRequest


@dataclass(frozen=True)
class OpenRouterCallMetadata:
    provider: str
    model: str
    latency_ms: int
    prompt_version: str
    schema_version: int | None
    usage: dict[str, int | float] | None
    failure_category: str | None


class OpenRouterBudgetError(ValueError):
    """No paid request may proceed under the current key allowance."""


class OpenRouterClient:
    def __init__(self, settings: LLMSettings, *, transport: httpx.AsyncBaseTransport | None = None):
        if settings.provider != "openrouter" or not settings.api_key:
            raise LLMConfigurationError("OpenRouter requires its own API key")
        if settings.model != "google/gemini-2.5-flash":
            raise LLMConfigurationError("The paid evaluation pins google/gemini-2.5-flash")
        self._settings = settings
        self._transport = transport
        self._lock = asyncio.Lock()
        self.call_metadata: list[OpenRouterCallMetadata] = []

    async def complete(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        started = monotonic()
        usage = None
        failure = None
        try:
            payload = {
                "model": self._settings.model,
                "messages": [
                    {"role": "system", "content": request.system},
                    *[
                        {"role": "user" if m.role == "shopper" else m.role, "content": m.content}
                        for m in request.messages
                    ],
                ],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
                "reasoning": {"enabled": False},
                "provider": {
                    "require_parameters": True,
                    "max_price": {"prompt": 0.3, "completion": 2.5},
                },
            }
            if request.tools:
                raise ValueError("Paid intent evaluation does not use tools")
            if request.response_schema is not None:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "shopping_intent",
                        "strict": True,
                        "schema": dict(request.response_schema),
                    },
                }
            # Conservative byte-based reservation, including schema and protocol overhead.
            reserve = (
                (len(json.dumps(payload).encode()) + 4096) * 0.3 + request.max_tokens * 2.5
            ) / 1_000_000
            if request.max_tokens <= 0 or request.max_tokens > 2048 or reserve > 0.02:
                raise OpenRouterBudgetError("Request exceeds the evaluation budget size bound")
            async with (
                self._lock,
                httpx.AsyncClient(
                    transport=self._transport,
                    timeout=self._settings.timeout_seconds,
                    headers={
                        "Authorization": f"Bearer {self._settings.api_key.get_secret_value()}"
                    },
                ) as client,
            ):
                key_response = await client.get("https://openrouter.ai/api/v1/key")
                key_response.raise_for_status()
                key = key_response.json().get("data", {})
                limit, remaining = key.get("limit"), key.get("limit_remaining")
                if (
                    not all(
                        isinstance(v, int | float) and not isinstance(v, bool) and isfinite(v)
                        for v in (limit, remaining)
                    )
                    or not 0 < limit <= 0.25
                    or remaining < reserve
                    or key.get("limit_reset") is not None
                ):
                    raise OpenRouterBudgetError(
                        "OpenRouter evaluation budget requires a non-resetting key limit "
                        "<= $0.25 and sufficient remaining credit"
                    )
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions", json=payload
                )
                response.raise_for_status()
            body = response.json()
            try:
                raw_usage = body.get("usage", {})
                usage = {
                    k: v
                    for k, v in raw_usage.items()
                    if k in {"prompt_tokens", "completion_tokens", "total_tokens", "cost"}
                    and isinstance(v, int | float)
                }
                choice = body["choices"][0]
                text = choice["message"]["content"]
                if choice.get("finish_reason") != "stop" or not isinstance(text, str) or not text:
                    raise ValueError("OpenRouter returned incomplete or non-text output")
            except (KeyError, IndexError, TypeError, AttributeError) as error:
                raise ValueError("OpenRouter returned invalid output") from error
            if request.response_validator:
                request.response_validator(text)
            yield LLMChunk(text=text)
        except Exception as error:
            failure = (
                "budget"
                if isinstance(error, OpenRouterBudgetError)
                else "throttled"
                if isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 429
                else "http"
                if isinstance(error, httpx.HTTPStatusError)
                else "timeout"
                if isinstance(error, httpx.TimeoutException)
                else "network"
                if isinstance(error, httpx.TransportError)
                else "invalid_response"
            )
            raise
        finally:
            self.call_metadata.append(
                OpenRouterCallMetadata(
                    "openrouter",
                    self._settings.model,
                    int((monotonic() - started) * 1000),
                    request.prompt_version,
                    request.schema_version,
                    usage,
                    failure,
                )
            )
