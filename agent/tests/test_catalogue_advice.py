import json

from agent.app import create_app
from agent.catalogue_contract import SearchQuery
from agent.llm import LLMSettings
from agent.tests.http_client import TestClient
from agent.tests.test_advice import RecordingModel, advice, decision
from agent.tests.test_catalogue_retrieval import Reads
from agent.tests.test_sessions import parse_sse
from agent.tests.test_step import home_snapshot


def test_retrieved_unknown_exclusion_stays_alternative_and_advisor_sees_fresh_facts():
    query = SearchQuery(
        query="something unusual",
        requirements=[{"field": "feature", "op": "exclude", "value": "leather"}],
        unverified_requirements=["washable"],
    )
    model = RecordingModel(
        {"kind": "search", "query": query.model_dump()},
        {"kind": "finish", "intent": decision(constraints={}), "selected_ids": ["p-4"]},
        advice("Material is unverified; this is only an alternative.", ["p-4"]),
    )
    reads = Reads()
    app = create_app(
        llm_settings=LLMSettings(provider="groq", model="test"),
        llm_client=model,
        catalogue_client=reads,
        catalogue_retrieval_enabled=True,
    )
    with TestClient(app) as client:
        sid = client.post("/sessions").json()["session_id"]
        response = client.post(
            f"/sessions/{sid}/messages",
            json={"text": "مش عاوزه جلد وعاوزه تتغسل", "snapshot": home_snapshot()},
        )
        assert response.status_code == 202
        events = parse_sse(client.get(f"/sessions/{sid}/events?once=true").text)
        cards = next(e["data"] for e in events if e["event"] == "suggestions")
        assert cards["exact_count"] is None
        assert cards["suggestions"][0]["id"] == "p-4"
        assert cards["suggestions"][0]["label"] == "alternative"
        assert "washable" in cards["suggestions"][0]["unmet"]
        context = json.loads(model.requests[-1].messages[0].content)
        assert context["products"][0]["price"]["amount"] == "20"
        assert context["products"][0]["eligibility"]["label"] == "alternative"
        assert len(model.requests) == 3


def test_no_category_no_vocabulary_whitelist_and_no_reads_for_navigation():
    model = RecordingModel(
        {
            "kind": "finish",
            "intent": decision(intent="navigate", constraints={"target": "account"}),
            "selected_ids": [],
        }
    )
    reads = Reads()
    app = create_app(
        llm_settings=LLMSettings(provider="groq", model="test"),
        llm_client=model,
        catalogue_client=reads,
        catalogue_retrieval_enabled=True,
    )
    with TestClient(app) as client:
        sid = client.post("/sessions").json()["session_id"]
        client.post(
            f"/sessions/{sid}/messages", json={"text": "my acount plz", "snapshot": home_snapshot()}
        )
        events = parse_sse(client.get(f"/sessions/{sid}/events?once=true").text)
        assert any(e["event"] == "action" for e in events)
        assert not reads.calls
