"""Evaluation-only Agent entrypoint; exposes redacted call metrics, never prompts or keys."""

import asyncio
import json
import os
from dataclasses import asdict, replace
from time import perf_counter

from agent.app import create_app
from agent.llm import build_llm_client, load_llm_settings


class MeasuredClient:
    def __init__(self, client):
        self.client = client
        self.calls = []
        self.release = asyncio.Event()
        self.release.set()

    async def complete(self, request):
        start = perf_counter()
        previous = len(getattr(self.client, "call_metadata", []))
        failure = None
        diagnostic = {}
        validator = request.response_validator

        def validate(text):
            try:
                intent = validator(text) if validator else None
            except Exception as error:
                if hasattr(error, "errors"):
                    diagnostic["schema_errors"] = [
                        {"type": item["type"], "path": item["loc"], "message": item["msg"]}
                        for item in error.errors(include_input=False, include_context=False)
                    ]
                raise
            if intent is not None:
                # Numeric IDs and operation enums only, never rejected text or page values.
                diagnostic.update(
                    intent=intent.intent,
                    operation=intent.cart_operation,
                    quantity=intent.cart_quantity,
                    mode=intent.cart_quantity_mode,
                    target_id=intent.cart_target_id,
                    category=intent.constraints.category,
                    product_type=intent.constraints.product_type,
                    request_mode=intent.request_mode,
                    needs_clarification=intent.needs_clarification,
                    missing_fields=intent.missing_fields,
                )
                context_text = request.system.split("Shopping Copilot intent context: ", 1)[-1]
                context, _ = json.JSONDecoder().raw_decode(context_text)
                diagnostic["observed_operation_targets"] = [
                    {"id": e["id"], "operation": e.get("form_action")}
                    for e in (context.get("current_snapshot") or {}).get("elements", [])
                    if e.get("role") == "button" and e.get("form_action", "").startswith("/cart/")
                ]
            return intent

        try:
            async for chunk in self.client.complete(replace(request, response_validator=validate)):
                await self.release.wait()
                yield chunk
        except Exception as error:
            failure = type(error).__name__
            raise
        finally:
            metadata = getattr(self.client, "call_metadata", [])[previous:]
            self.calls.append(
                {
                    "elapsed_ms": metadata[-1].latency_ms
                    if metadata
                    else (perf_counter() - start) * 1000,
                    "ttft_ms": getattr(metadata[-1], "ttft_ms", None) if metadata else None,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "prompt_version": request.prompt_version,
                    "schema_version": request.schema_version,
                    "failure": failure,
                    "diagnostic": diagnostic,
                    "usage": asdict(metadata[-1])["usage"] if metadata else None,
                }
            )


if os.environ.get("MILESTONE_EVAL") != "1":
    raise RuntimeError("This entrypoint is only for explicit local milestone evaluation")
settings = replace(load_llm_settings(), stream=True)
client = MeasuredClient(build_llm_client(settings))
app = create_app(llm_settings=settings, llm_client=client)


@app.get("/__eval/metrics")
def metrics():
    return {"provider": settings.provider, "model": settings.model, "calls": client.calls}


@app.post("/__eval/hold")
async def hold():
    client.release.clear()
    return {"held": True}


@app.post("/__eval/release")
async def release():
    client.release.set()
    return {"held": False}
