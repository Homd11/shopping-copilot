"""Prepare a retrieval turn; publishing remains owned by the active Session task."""

import asyncio
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from agent.advice import (
    AdviceEvidence,
    build_advice_request,
    compose_advice,
    prepare_retrieved_advice,
)
from agent.catalogue import DiscoveryResult
from agent.catalogue_client import CatalogueClient
from agent.catalogue_retrieval import RetrievalBudget, RetrievalExhausted, retrieve_products
from agent.llm.intent import StructuredIntent


@lru_cache(maxsize=1)
def _encoder(cache):
    from agent.catalogue_embedding import CatalogueEncoder

    return CatalogueEncoder(Path(cache))


async def configured_client(config):
    ranking = os.environ.get("CATALOGUE_RANKING", "lexical")
    if ranking not in {"lexical", "hybrid"}:
        raise ValueError("Invalid catalogue ranking")
    encoder = None
    if ranking == "hybrid":
        cache = os.environ.get("CATALOGUE_MODEL_CACHE")
        if not cache:
            raise ValueError("Hybrid requires a pre-populated local model cache")
        encoder = await asyncio.to_thread(_encoder, cache)
    return CatalogueClient(secret=config["secret"], origin=config["private_url"], encoder=encoder)


@dataclass
class PreparedTurn:
    intent: StructuredIntent
    evidence: AdviceEvidence | None
    summary: str | None
    references: list[dict[str, str]]


async def prepare_turn(task, snapshot, storefront, llm, catalogue, ensure_active):
    if task.retrieval_budget is None:
        task.retrieval_budget = RetrievalBudget()
    outcome = await retrieve_products(
        task.message,
        task.resolved_state,
        llm,
        catalogue,
        ensure_active,
        storefront=storefront,
        snapshot=snapshot,
        budget=task.retrieval_budget,
    )
    await ensure_active()
    if outcome.question:
        intent = StructuredIntent.model_validate(
            {
                "v": 9,
                "language": outcome.language,
                "dialect": "unknown",
                "intent": "advice",
                "constraints": {},
                "missing_fields": [],
                "needs_clarification": False,
            }
        )
        return PreparedTurn(
            intent, AdviceEvidence(DiscoveryResult(None, ()), ()), outcome.question, []
        )
    intent = outcome.intent
    references = [
        {
            "id": p.product.id,
            "name": p.product.nameAr if intent.language == "ar" else p.product.nameEn,
        }
        for p in outcome.products
    ]
    if intent.intent not in {"find_products", "advice"} or intent.needs_clarification:
        return PreparedTurn(intent, None, None, references)
    evidence = prepare_retrieved_advice(outcome)
    if outcome.budget.advice >= 1:
        raise RetrievalExhausted("Advice completion already attempted for this message")
    await ensure_active()
    outcome.budget.advice += 1
    summary = await compose_advice(
        llm,
        build_advice_request(task.message, intent, evidence, task.resolved_state, snapshot),
        evidence,
    )
    await ensure_active()
    return PreparedTurn(intent, evidence, summary, references)
