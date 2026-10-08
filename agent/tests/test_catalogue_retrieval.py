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


def test_initial_filter_is_preserved_without_requiring_duplicate_model_fields():
    size = {"field": "size", "op": "eq", "value": "43"}
    model = RecordingModel(
        {"kind": "search", "query": {"query": "football", "predicates": [size]}},
        {"kind": "search", "query": {"query": "shoes", "requirements": []}},
        {"kind": "finish", "intent": decision(constraints={}), "selected_ids": ["p-4"]},
    )
    reads = Reads()
    result = asyncio.run(run(model, reads))
    assert len(reads.calls) == 3
    assert result.selected_ids == ["p-4"]
    for query in reads.calls:
        assert [p.model_dump() for p in query.requirements] == [size]


def test_freezing_initial_filters_keeps_explicit_exclusions_and_deduplicates():
    size = {"field": "size", "op": "eq", "value": "43"}
    excluded = {"field": "feature", "op": "exclude", "value": "leather"}

    class EmptyReads(Reads):
        async def search(self, query):
            self.calls.append(query)
            return SearchResult(
                v=1,
                catalogue_revision=1,
                candidates=[],
                ranking="lexical",
                exact_count=0,
                truncated=False,
                next_cursor=None,
                unverified_requirements=[],
            )

    model = RecordingModel(
        {
            "kind": "search",
            "query": {"query": "shoes", "predicates": [size], "requirements": [excluded, size]},
        },
        {"kind": "finish", "intent": decision(constraints={}), "selected_ids": []},
    )
    reads = EmptyReads()
    asyncio.run(run(model, reads))
    assert [p.model_dump() for p in reads.calls[0].requirements] == [excluded, size]


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


@pytest.mark.parametrize("provider", ["groq", "nvidia"])
def test_provider_http_retries_cannot_escape_coordinator_budget(provider):
    import httpx

    from agent.llm import load_llm_settings
    from agent.llm.groq import GroqClient
    from agent.llm.nvidia import NvidiaNIMClient

    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(500, json={"error": "fixture failure"})

    settings = load_llm_settings(
        {
            "LLM_PROVIDER": provider,
            "LLM_MODEL": "fixture",
            ("GROQ_API_KEY" if provider == "groq" else "NVIDIA_API_KEY"): "fixture-key",
        }
    )
    client = (GroqClient if provider == "groq" else NvidiaNIMClient)(
        settings, transport=httpx.MockTransport(handler)
    )
    budget = RetrievalBudget()
    for _ in range(3):
        with pytest.raises(httpx.HTTPStatusError):
            asyncio.run(run(client, Reads(), budget=budget))
    with pytest.raises(RetrievalExhausted):
        asyncio.run(run(client, Reads(), budget=budget))
    assert len(calls) == budget.decisions == 3


@pytest.mark.parametrize("malformed_first", [False, True])
def test_real_openrouter_adapter_accepts_retrieval_requests_within_existing_cap(malformed_first):
    import httpx

    from agent.catalogue_contract import SearchQuery
    from agent.llm.openrouter import OpenRouterClient
    from agent.tests.test_openrouter import settings

    answers = iter(
        [
            *([{}] if malformed_first else []),
            {
                "kind": "search",
                "query": SearchQuery(
                    query="football", requirements=[{"field": "size", "op": "eq", "value": "43"}]
                ).model_dump(),
            },
            {"kind": "finish", "intent": decision(constraints={}), "selected_ids": ["p-4"]},
        ]
    )
    methods = []

    def handler(request):
        methods.append(request.method)
        if request.method == "GET":
            return httpx.Response(
                200, json={"data": {"limit": 0.25, "limit_remaining": 0.25, "limit_reset": None}}
            )
        schema = json.loads(request.content)["response_format"]["json_schema"]["schema"]
        # Replay the observed provider rejection for unresolved union references.
        if schema["oneOf"][0].get("$ref"):
            return httpx.Response(
                400, json={"error": {"message": "reference to undefined schema at oneOf.0"}}
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(next(answers))}}
                ]
            },
        )

    client = OpenRouterClient(settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(run(client, Reads()))
    assert result.selected_ids == ["p-4"]
    assert result.budget.decisions == 2 + int(malformed_first) and result.budget.reads == 2
    assert methods == ["GET", "POST"] * (2 + int(malformed_first))


@pytest.mark.parametrize("failure_kind", ["budget", "configuration"])
def test_provider_failure_is_not_retried_as_bad_language_output(failure_kind):
    from agent.llm.config import LLMConfigurationError
    from agent.llm.openrouter import OpenRouterBudgetError

    error_type = OpenRouterBudgetError if failure_kind == "budget" else LLMConfigurationError
    calls = []

    class BudgetBlocked:
        async def complete(self, request):
            calls.append(request)
            raise error_type("Fixture operational failure")
            yield

    with pytest.raises(error_type):
        asyncio.run(run(BudgetBlocked(), Reads()))
    assert len(calls) == 1
