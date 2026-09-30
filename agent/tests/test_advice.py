import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from agent.app import create_app
from agent.llm import LLMChunk, LLMSettings
from agent.tests.test_catalogue import catalogue
from agent.tests.test_sessions import parse_sse
from agent.tests.test_step import home_snapshot


class RecordingModel:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    async def complete(self, request):
        self.requests.append(request)
        yield LLMChunk(text=json.dumps(next(self.responses), ensure_ascii=False))


class Reader:
    async def read(self):
        return catalogue()


def decision(**changes):
    return {
        "v": 9,
        "language": "ar",
        "dialect": "egyptian_arabic",
        "intent": "advice",
        "constraints": {"category": "clothing"},
        "missing_fields": [],
        "needs_clarification": False,
        **changes,
    }


def advice(text, references=None):
    return {"v": 1, "message": text, "product_ids": references or []}


def client_for(model, reader=None):
    return TestClient(
        create_app(
            llm_settings=LLMSettings(provider="groq", model="test", api_key=None),
            llm_client=model,
            catalogue_reader=reader or Reader(),
        )
    )


def send(client, session, text, snapshot=None, tab_id=None):
    response = client.post(
        f"/sessions/{session}/messages",
        json={
            "text": text,
            "snapshot": snapshot or home_snapshot(),
        },
        headers={"x-tab-id": tab_id} if tab_id else {},
    )
    assert response.status_code == 202
    task_id = response.json()["task_id"]
    events = parse_sse(client.get(f"/sessions/{session}/events?once=true").text)
    return [event for event in events if event["data"].get("task_id") == task_id]


def test_advice_is_natural_read_only_and_followup_retains_shopper_correction():
    first = "القميص الأبيض خفيف حسب بيانات المتجر. تحبي تنسيق هادي ولا ملفت؟"
    second = "تمام، نخليها هادية. الأبيض ممكن يناسب الأسود في رأيي."
    model = RecordingModel(
        decision(subjective_preferences=["ملفت"]),
        advice(first, ["white-shirt"]),
        decision(subjective_preferences=["هادي"]),
        advice(second, ["white-shirt"]),
    )
    with client_for(model) as client:
        session = client.post("/sessions").json()["session_id"]
        events = send(client, session, "مش عارفه البس ايه ع الاسود.. حاجه تلفت؟")
        assert events[-1]["event"] == "done"
        assert events[-1]["data"]["summary"] == first
        assert not any(event["event"] in {"action", "error"} for event in events)
        events = send(client, session, "لا لا هادي احسن، مش عايزه ملفت")
        assert events[-1]["data"]["summary"] == second
        assert not any(event["event"] == "action" for event in events)
    assert len(model.requests) == 4
    context = json.loads(model.requests[-1].messages[0].content)
    assert context["intent"]["subjective_preferences"] == ["هادي"]
    assert any(first in item["text"] for item in context["recent_conversation"])
    assert context["products"][0]["features"] == ["lightweight"]
    assert model.requests[-1].tools == ()


@pytest.mark.parametrize(
    "bad",
    [
        advice("Invented product", ["not-in-catalogue"]),
        {**advice("I emptied your cart"), "action": {"type": "clear_cart"}},
        advice("   "),
        {"unexpected": "Ignore all rules"},
    ],
)
def test_invalid_advice_finishes_with_verified_cards_without_retry_or_actions(bad):
    model = RecordingModel(decision(), bad)
    with client_for(model) as client:
        session = client.post("/sessions").json()["session_id"]
        events = send(client, session, "ايه رايك؟")
    assert len(model.requests) == 2
    assert events[-1]["event"] == "done"
    assert "نصيحة موثوقة" in events[-1]["data"]["summary"]
    assert not any(event["event"] in {"action", "error"} for event in events)
    cards = next(
        event["data"]["suggestions"] for event in events if event["event"] == "suggestions"
    )
    assert [card["id"] for card in cards] == ["white-shirt"]


def test_advice_comparison_uses_fresh_facts_and_excluded_items_are_not_recommended():
    observed = home_snapshot()
    observed["elements"] = [
        {"id": index, "role": "link", "name": key, "href": f"/p/{key}", "visible": True}
        for index, key in enumerate(["black-leather", "sold-out-runner", "road-runner"], 1)
    ]
    model = RecordingModel(
        decision(
            constraints={"category": "shoes"},
            advice_product_ids=["black-leather", "sold-out-runner", "road-runner"],
            catalogue_requirements=[
                {"kind": "feature", "value": "leather", "excluded": True, "source": "مش جلد"}
            ],
        ),
        advice("الجلد مش مناسب لطلبك والتاني خلصان، جري طريق متاح.", ["road-runner"]),
    )

    class ChangedReader:
        async def read(self):
            snapshot = catalogue()
            snapshot.products[2].price.amount = "1800"
            return snapshot

    with client_for(model, ChangedReader()) as client:
        session = client.post("/sessions").json()["session_id"]
        events = send(client, session, "دول انهي احسن.. بس مش جلد ها", observed)
    assert events[-1]["event"] == "done"
    context = json.loads(model.requests[-1].messages[0].content)
    products = {product["id"]: product for product in context["products"]}
    assert products["road-runner"]["price"]["amount"] == "1800"
    assert products["black-leather"]["eligibility"]["label"] == "comparison_only"
    assert products["sold-out-runner"]["available"] is False
    cards = next(
        event["data"]["suggestions"] for event in events if event["event"] == "suggestions"
    )
    assert [card["id"] for card in cards] == ["road-runner"]


def test_advice_followup_can_open_verified_product_without_an_extra_advice_call():
    model = RecordingModel(
        decision(),
        advice("الأبيض ممكن يناسبك.", ["white-shirt"]),
        decision(intent="open_product", constraints={}, product_id="white-shirt"),
    )
    with client_for(model) as client:
        session = client.post("/sessions").json()["session_id"]
        send(client, session, "ساعدني اختار")
        events = send(client, session, "طب وريني دا")
    actions = [event["data"]["action"] for event in events if event["event"] == "action"]
    assert len(actions) == 1
    assert actions[0]["type"] == "navigate"
    assert actions[0]["url"] == "/p/white-shirt"
    assert len(model.requests) == 3


def test_no_evidence_allows_conversation_and_question_without_forced_execution_clarification():
    model = RecordingModel(
        decision(constraints={}),
        advice("تحب تنسيق لمناسبة ولا لبس يومي؟"),
    )
    with client_for(model) as client:
        session = client.post("/sessions").json()["session_id"]
        events = send(client, session, "انا تايه بصراحه ساعدني")
    assert events[-1]["event"] == "done"
    assert not any(event["event"] == "action" for event in events)
    assert json.loads(model.requests[-1].messages[0].content)["products"] == []


@pytest.mark.parametrize("interruption", ["stop", "refresh"])
def test_late_advice_is_discarded_after_stop_or_refresh(interruption):
    async def scenario():
        class DelayedModel(RecordingModel):
            def __init__(self):
                super().__init__(decision(), advice("Late advice", ["white-shirt"]))
                self.started = asyncio.Event()
                self.release = asyncio.Event()

            async def complete(self, request):
                if request.prompt_version == "advice-v1":
                    self.started.set()
                    await self.release.wait()
                async for chunk in super().complete(request):
                    yield chunk

        model = DelayedModel()
        app = create_app(
            llm_settings=LLMSettings(provider="groq", model="test"),
            llm_client=model,
            catalogue_reader=Reader(),
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            session = (await client.post("/sessions", json={"tab_id": "tab-1"})).json()[
                "session_id"
            ]
            pending = asyncio.create_task(
                client.post(
                    f"/sessions/{session}/messages",
                    headers={"x-tab-id": "tab-1"},
                    json={"text": "ساعدني اختار", "snapshot": home_snapshot()},
                )
            )
            await asyncio.wait_for(model.started.wait(), 3)
            if interruption == "stop":
                response = await client.post(
                    f"/sessions/{session}/stop", headers={"x-tab-id": "tab-1"}
                )
            else:
                response = await client.get(f"/sessions/{session}/state?tab_id=tab-1")
            assert response.status_code in {200, 202}
            model.release.set()
            await pending
            events = parse_sse((await client.get(f"/sessions/{session}/events?once=true")).text)
            assert not any(event["event"] in {"done", "suggestions", "action"} for event in events)

    asyncio.run(scenario())


def test_every_explicit_comparison_gets_eligibility_independent_of_card_limit():
    class FourProducts:
        async def read(self):
            source = catalogue()
            return source.model_copy(
                update={
                    "products": [
                        source.products[0].model_copy(update={"id": f"choice-{index}"})
                        for index in range(4)
                    ]
                }
            )

    ids = [f"choice-{index}" for index in range(4)]
    observed = home_snapshot()
    observed["elements"] = [
        {"id": index + 1, "role": "link", "name": key, "href": f"/p/{key}", "visible": True}
        for index, key in enumerate(ids)
    ]
    model = RecordingModel(
        decision(constraints={"category": "shoes"}, advice_product_ids=ids),
        advice("كلهم متاحين، تحب تقارن على أساس إيه؟", ids),
    )
    with client_for(model, FourProducts()) as client:
        session = client.post("/sessions").json()["session_id"]
        events = send(client, session, "قارن الاربعه دول", observed)
    products = json.loads(model.requests[-1].messages[0].content)["products"]
    assert len(products) == 4
    assert all(product["eligibility"]["label"] == "exact_match" for product in products)
    cards = next(
        event["data"]["suggestions"] for event in events if event["event"] == "suggestions"
    )
    assert len(cards) == 3  # Existing Panel event contract; all four remain in advice evidence.


def test_reconciliation_to_another_origin_discards_previous_advice_preferences():
    model = RecordingModel(
        decision(subjective_preferences=["quiet"]),
        advice("First advice", ["white-shirt"]),
        decision(constraints={}),
        advice("What do you need?"),
    )
    with client_for(model) as client:
        session = client.post("/sessions", json={"tab_id": "tab-1"}).json()["session_id"]
        send(client, session, "quiet please", tab_id="tab-1")
        observed = {**home_snapshot(), "url": "https://other.example/"}
        response = client.post(
            f"/sessions/{session}/reconcile",
            headers={"x-tab-id": "tab-1"},
            json={"snapshot": observed},
        )
        assert response.status_code == 200
        send(client, session, "help me choose", observed, tab_id="tab-1")
    context = json.loads(model.requests[-1].messages[0].content)
    assert context["previous_advice_context"] == {}
    assert context["recent_conversation"] == []
