import asyncio
import json

import pytest

from agent.catalogue_contract import Candidate, DetailsResult, SearchQuery, SearchResult
from agent.catalogue_retrieval import RetrievalBudget, RetrievalExhausted, retrieve_products
from agent.llm.contract import LLMChunk
from agent.planner import ScriptedPlanner
from agent.tests.test_advice import RecordingModel, decision


def candidate(key="p-4", status=None):
    return Candidate.model_validate(
        {
            "product": {
                "id": key,
                "category": "clothing",
                "nameAr": "قطعة",
                "nameEn": "Piece",
                "type": "shirt",
                "price": {"amount": "20", "currency": "EGP"},
                "sizes": ["M"],
                "colors": ["purple"],
                "available": True,
                "addedAt": "2026-01-01",
                "features": [],
                "suitableFor": [],
                "wearPosition": "upper",
                "absent_features": [],
                "absent_uses": [],
            },
            "product_revision": 1,
            "requirements": [] if status is None else [{"index": 0, "status": status}],
        }
    )


class Reads:
    def __init__(self):
        self.calls = []

    async def search(self, query):
        self.calls.append(query)
        return SearchResult(
            v=1,
            catalogue_revision=1,
            candidates=[
                candidate(f"p-{i}", "unknown" if query.requirements else None) for i in range(5)
            ],
            ranking="lexical",
            exact_count=None,
            next_cursor=None,
            truncated=False,
            unverified_requirements=query.unverified_requirements,
        )

    async def details(self, query):
        self.calls.append(query)
        return DetailsResult(
            v=1,
            catalogue_revision=1,
            products=[candidate(k, "unknown" if query.requirements else None) for k in query.ids],
            missing_ids=[],
            unverified_requirements=query.unverified_requirements,
        )


async def active():
    pass


def run(model, reads, **kwargs):
    return retrieve_products(
        "مش لازم الكلام يبقى مظبوط",
        {},
        model,
        reads,
        active,
        storefront=ScriptedPlanner().storefront,
        **kwargs,
    )


def test_model_selects_beyond_three_and_refreshes_selection():
    model = RecordingModel(
        {"kind": "search", "query": SearchQuery(query="purple shirt").model_dump()},
        {"kind": "finish", "intent": decision(constraints={}), "selected_ids": ["p-4"]},
    )
    reads = Reads()
    outcome = asyncio.run(run(model, reads))
    assert outcome.selected_ids == ["p-4"]
    assert outcome.budget.decisions == 2 and outcome.budget.reads == 2
    assert reads.calls[-1].ids == ["p-4"]
    assert "catalogue_values" not in model.requests[0].messages[0].content


def test_direct_navigation_has_no_reads_and_preserves_action_validation():
    model = RecordingModel(
        {
            "kind": "finish",
            "intent": decision(intent="navigate", constraints={"target": "cart"}),
            "selected_ids": [],
        }
    )
    reads = Reads()
    outcome = asyncio.run(run(model, reads))
    assert outcome.intent.intent == "navigate" and not reads.calls


def test_failed_decisions_and_retries_share_three_attempt_budget():
    budget = RetrievalBudget()
    model = RecordingModel({}, {}, {}, {})
    with pytest.raises(RetrievalExhausted):
        asyncio.run(run(model, Reads(), budget=budget))
    with pytest.raises(RetrievalExhausted):
        asyncio.run(run(model, Reads(), budget=budget))
    assert len(model.requests) == 3 and budget.decisions == 3


def test_requirements_cannot_disappear_on_refinement():
    query = SearchQuery(
        query="bag", requirements=[{"field": "feature", "op": "exclude", "value": "leather"}]
    )
    model = RecordingModel(
        {"kind": "search", "query": query.model_dump()},
        {"kind": "search", "query": SearchQuery(query="fabric bag").model_dump()},
        {"kind": "finish", "intent": decision(constraints={}), "selected_ids": ["p-4"]},
    )
    reads = Reads()
    outcome = asyncio.run(run(model, reads))
    assert all(call.requirements == query.requirements for call in reads.calls)
    assert outcome.products[0].requirements[0].status == "unknown"


def test_stop_discards_late_model_completion():
    async def scenario():
        stopped = False

        async def ensure():
            if stopped:
                raise asyncio.CancelledError()

        class Model:
            async def complete(self, request):
                nonlocal stopped
                stopped = True
                yield LLMChunk(
                    text=json.dumps({"kind": "finish", "intent": decision(), "selected_ids": []})
                )

        with pytest.raises(asyncio.CancelledError):
            await retrieve_products(
                "request", {}, Model(), Reads(), ensure, storefront=ScriptedPlanner().storefront
            )

    asyncio.run(scenario())
