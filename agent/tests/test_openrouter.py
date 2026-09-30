import asyncio
import json
from dataclasses import replace

import httpx
import pytest

from agent.llm.config import load_llm_settings
from agent.llm.contract import LLMMessage, LLMRequest
from agent.llm.openrouter import OpenRouterClient


def collect(client):
    async def run():
        return [
            c.text
            async for c in client.complete(
                LLMRequest(
                    system="Extract intent",
                    messages=(LLMMessage("shopper", "add"),),
                    response_schema={"type": "object"},
                    response_validator=json.loads,
                )
            )
        ]

    return asyncio.run(run())


def settings():
    return load_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "test-secret",
        }
    )


@pytest.mark.parametrize("cap", ["1.00", "1.01", "nan", "inf", "0"])
def test_explicit_total_cap_is_bounded_by_owner_authorized_dollar(cap):
    environment = {
        "LLM_PROVIDER": "openrouter",
        "LLM_MODEL": "google/gemini-2.5-flash",
        "OPENROUTER_API_KEY": "test-secret",
        "OPENROUTER_TOTAL_CAP_DOLLARS": cap,
    }
    if cap == "1.00":
        assert load_llm_settings(environment).openrouter_total_limit == 1.00
    else:
        with pytest.raises(ValueError):
            load_llm_settings(environment)


@pytest.mark.parametrize("has_usage", [True, False])
def test_error_stream_retains_identity_and_received_usage_without_emitting(has_usage):
    calls = []

    def handler(request):
        calls.append(request.method)
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200, json={"data": {"limit": 0.25, "limit_remaining": 0.25, "limit_reset": None}}
            )
        event = {"id": "gen-failed-attempt", "error": {"message": "private provider detail"}}
        if has_usage:
            event["usage"] = {"cost": 0.0001, "prompt_tokens": 12, "completion_tokens": 2}
        return httpx.Response(200, text="data: " + json.dumps(event) + "\n\n")

    client = OpenRouterClient(
        replace(settings(), stream=True), transport=httpx.MockTransport(handler)
    )
    with pytest.raises(ValueError):
        collect(client)
    metadata = client.call_metadata[-1]
    assert metadata.generation_id == "gen-failed-attempt"
    assert metadata.attempt_id
    assert metadata.started_at.endswith("+00:00")
    assert metadata.usage == (
        {"cost": 0.0001, "prompt_tokens": 12, "completion_tokens": 2} if has_usage else None
    )
    assert "private provider detail" not in repr(metadata)
    assert calls == ["GET", "POST"]


@pytest.mark.parametrize("terminal", ["stop", "length", "error", None])
def test_stream_is_buffered_until_complete_validation_and_records_first_content(terminal):
    def handler(request):
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "limit": 0.25,
                        "limit_remaining": 0.25,
                        "limit_reset": None,
                    }
                },
            )
        assert json.loads(request.content)["stream"] is True
        chunks = [
            {"choices": [{"delta": {"role": "assistant"}}]},
            {"choices": [{"delta": {"content": '{"ok":'}}]},
            {"choices": [{"delta": {"content": "true}"}, "finish_reason": terminal}]},
            {"choices": [], "usage": {"cost": 0.001, "prompt_tokens": 2, "completion_tokens": 3}},
        ]
        content = ": keepalive\n\n" + "".join("data: " + json.dumps(c) + "\n\n" for c in chunks)
        content += "data: [DONE]\n\n"
        return httpx.Response(200, text=content)

    client = OpenRouterClient(
        replace(settings(), stream=True), transport=httpx.MockTransport(handler)
    )
    if terminal == "stop":
        assert collect(client) == ['{"ok":true}']
        assert client.call_metadata[-1].ttft_ms is not None
        assert client.call_metadata[-1].usage["cost"] == 0.001
    else:
        with pytest.raises(ValueError):
            collect(client)
        assert client.call_metadata[-1].ttft_ms is not None
        assert client.call_metadata[-1].usage["cost"] == 0.001


def test_bounded_openrouter_request_validates_output_and_records_cost():
    def handler(request):
        assert request.headers["authorization"] == "Bearer test-secret"
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "limit": 0.25,
                        "limit_remaining": 0.25,
                        "limit_reset": None,
                        "usage": 0,
                    }
                },
            )
        payload = json.loads(request.content)
        assert payload["model"] == "google/gemini-2.5-flash"
        assert payload["reasoning"] == {"enabled": False}
        assert payload["provider"]["max_price"] == {"prompt": 0.3, "completion": 2.5}
        assert payload["provider"]["require_parameters"] is True
        assert payload["response_format"]["json_schema"]["strict"] is True
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}],
                "usage": {"cost": 0.001},
            },
        )

    client = OpenRouterClient(settings(), transport=httpx.MockTransport(handler))
    assert collect(client) == ['{"ok":true}']
    assert client.call_metadata[-1].usage["cost"] == 0.001


@pytest.mark.parametrize(
    "limit,remaining,reset", [(100, 100, None), (0.25, 0, None), (0.25, 0.25, "daily")]
)
def test_budget_check_blocks_paid_calls(limit, remaining, reset):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "data": {
                    "limit": limit,
                    "limit_remaining": remaining,
                    "limit_reset": reset,
                    "usage": 0,
                }
            },
        )

    with pytest.raises(ValueError, match="budget"):
        collect(OpenRouterClient(settings(), transport=httpx.MockTransport(handler)))
    assert calls == ["/api/v1/key"]


@pytest.mark.parametrize(
    "body",
    [
        {"choices": []},
        {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]},
        {"choices": [{"finish_reason": "stop", "message": {"content": "invalid-json"}}]},
        None,
        "malformed-envelope",
    ],
)
def test_invalid_completion_never_retries_or_emits_an_action(body):
    paid_calls = []

    def handler(request):
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200, json={"data": {"limit": 0.25, "limit_remaining": 0.25, "limit_reset": None}}
            )
        paid_calls.append(request)
        if body == "malformed-envelope":
            return httpx.Response(200, content=b"not-json")
        return httpx.Response(200, content=json.dumps(body))

    client = OpenRouterClient(settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        collect(client)
    assert len(paid_calls) == 1


def test_real_intent_request_fits_the_paid_budget_bound():
    from agent.llm import build_intent_request
    from agent.storefront import load_storefront_definition

    def handler(request):
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200, json={"data": {"limit": 0.25, "limit_remaining": 0.25, "limit_reset": None}}
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "v": 8,
                                    "language": "ar",
                                    "dialect": "egyptian_arabic",
                                    "intent": "cart_edit",
                                    "cart_operation": "add",
                                    "cart_source": "ضيفه للسلة",
                                    "constraints": {},
                                    "missing_fields": [],
                                    "needs_clarification": False,
                                }
                            )
                        },
                    }
                ]
            },
        )

    client = OpenRouterClient(settings(), transport=httpx.MockTransport(handler))
    request = build_intent_request(
        "ضيفه للسلة",
        storefront=load_storefront_definition(),
        resolved_state={},
        pending_clarification=None,
    )

    async def run():
        return [c async for c in client.complete(request)]

    assert len(asyncio.run(run())) == 1
