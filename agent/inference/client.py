"""Bounded provider-neutral complete() boundary; no language interpretation."""

import asyncio
import json
from contextlib import aclosing
from dataclasses import dataclass, replace
from decimal import Decimal
from math import isfinite
from uuid import uuid4

from agent.inference.ledger import InferenceRefused, units


def _expanded_schema(value, root, stack=()):
    if isinstance(value, list):
        return [_expanded_schema(item, root, stack) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        reference = value["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/") or reference in stack:
            raise InferenceRefused("unavailable")
        target = root
        for part in reference[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        expanded = _expanded_schema(target, root, (*stack, reference))
        return {
            **expanded,
            **_expanded_schema(
                {key: item for key, item in value.items() if key != "$ref"}, root, stack
            ),
        }
    return {
        key: _expanded_schema(item, root, stack) for key, item in value.items() if key != "$defs"
    }


@dataclass(frozen=True)
class InferencePrices:
    input_per_million: Decimal
    output_per_million: Decimal

    def __post_init__(self):
        if units(self.input_per_million) + units(self.output_per_million) <= 0:
            raise ValueError("Explicit positive inference prices are required")

    def reservation(self, request) -> Decimal:
        if request.tools or not 0 < request.max_tokens <= 2048:
            raise InferenceRefused("unavailable")
        schema = request.response_schema or {}
        try:
            body = json.dumps(
                {
                    "system": request.system,
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                    "response_schema": _expanded_schema(schema, schema),
                }
            ).encode()
        except (ValueError, KeyError, TypeError, RecursionError) as error:
            raise InferenceRefused("unavailable") from error
        if len(body) > 256_000:
            raise InferenceRefused("unavailable")
        # One input byte per token is deliberately conservative. Include protocol
        # overhead and fully expanded local schema references before reserving.
        return (
            Decimal(len(body) + 4096) * self.input_per_million
            + Decimal(request.max_tokens) * self.output_per_million
        ) / Decimal(1_000_000)


class GuardedClient:
    def __init__(
        self,
        client,
        ledger,
        prices: InferencePrices,
        *,
        receipt=None,
        maximum_active: int,
        maximum_waiting: int,
        wait_seconds: float,
    ):
        if (
            isinstance(maximum_active, bool)
            or not isinstance(maximum_active, int)
            or not 1 <= maximum_active <= 32
            or isinstance(maximum_waiting, bool)
            or not isinstance(maximum_waiting, int)
            or not 0 <= maximum_waiting <= 64
            or not isfinite(wait_seconds)
            or not 0 < wait_seconds <= 30
        ):
            raise ValueError("Finite inference concurrency and queue bounds are required")
        self.client, self.ledger, self.prices = client, ledger, prices
        self.receipt = receipt or (lambda _client, _attempt: None)
        self._semaphore = asyncio.Semaphore(maximum_active)
        self._admission_lock = asyncio.Lock()
        self._admitted = 0
        self._capacity = maximum_active + maximum_waiting
        self._wait_seconds = wait_seconds

    async def complete(self, request):
        async with self._admission_lock:
            if self._admitted >= self._capacity:
                raise InferenceRefused("busy")
            self._admitted += 1
        acquired = False
        try:
            try:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=self._wait_seconds)
            except TimeoutError as error:
                raise InferenceRefused("busy") from error
            acquired = True
            attempt = request.attempt_id or str(uuid4())
            bound = self.prices.reservation(request)
            await asyncio.to_thread(self.ledger.reserve, attempt, bound)
            chunks = []
            try:
                async with aclosing(
                    self.client.complete(
                        replace(request, attempt_id=attempt, provider_attempt_limit=1)
                    )
                ) as response:
                    async for chunk in response:
                        chunks.append(chunk)
            finally:
                cost = self.receipt(self.client, attempt)
                if cost is not None:
                    await asyncio.to_thread(self.ledger.settle, attempt, cost)
                else:
                    await asyncio.to_thread(self.ledger.ensure_accounted, attempt)
            # Do not expose a completion if durable settlement fails.
            for chunk in chunks:
                yield chunk
        finally:
            if acquired:
                self._semaphore.release()
            async with self._admission_lock:
                self._admitted -= 1
