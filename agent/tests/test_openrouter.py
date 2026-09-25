import asyncio
import json

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
                                    "v": 6,
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
