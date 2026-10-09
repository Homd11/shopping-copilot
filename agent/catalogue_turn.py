"""Prepare a retrieval turn; publishing remains owned by the active Session task."""

import asyncio
import os
from dataclasses import dataclass, replace
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


class CatalogueTurnInterrupted(Exception):
    pass


@dataclass
class PreparedTurn:
    intent: StructuredIntent
    evidence: AdviceEvidence | None
    summary: str | None
    references: list[dict[str, str]]


def _exhausted_turn(task):
    intent = StructuredIntent.model_validate(
        {
            "v": 9,
            "language": task.language,
            "dialect": "unknown",
            "intent": "advice",
            "constraints": {},
            "missing_fields": [],
            "needs_clarification": False,
        }
    )
    question = (
        "ما قدرتش أكمّل البحث في المحاولة دي. إيه أهم شرط نبدأ بيه؟"
        if task.language == "ar"
        else "I couldn't finish this search. Which requirement should we start with?"
    )
    return PreparedTurn(intent, AdviceEvidence(DiscoveryResult(None, ()), ()), question, [])


async def prepare_turn(task, snapshot, storefront, llm, catalogue, ensure_active):
    if task.retrieval_budget is None:
        task.retrieval_budget = RetrievalBudget()
    try:
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
    except RetrievalExhausted:
        await ensure_active()
        return _exhausted_turn(task)
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
    if outcome.advice_message is not None:
        return PreparedTurn(intent, evidence, outcome.advice_message, references)
    if outcome.budget.advice >= 1:
        return _exhausted_turn(task)
    await ensure_active()
    outcome.budget.advice += 1
    summary = await compose_advice(
        llm,
        replace(
            build_advice_request(task.message, intent, evidence, task.resolved_state, snapshot),
            provider_attempt_limit=1,
        ),
        evidence,
    )
    await ensure_active()
    return PreparedTurn(intent, evidence, summary, references)
