import asyncio
import json

import pytest

from agent.llm import LLMChunk, ScriptedLLMClient, interpret_message
from agent.llm.intent import StructuredIntent
from agent.schemas import Snapshot
from agent.sessions import SessionStore
from agent.storefront import load_storefront_definition
from agent.tests.test_real_task import intent_payload, real_client
from agent.tests.test_sessions import parse_sse
from agent.tests.test_step import home_snapshot


@pytest.mark.parametrize("message", ["افتح صفحة القميص الرسمي", "افتح صفحة قَمِيص رَسْمِي"])
def test_verified_product_reference_does_not_depend_on_model_source_metadata(message):
    # Captured provider output: the product is correct, navigation_source is omitted.
    payload = {
        "v": 7,
        "language": "ar",
        "dialect": "egyptian_arabic",
        "intent": "open_product",
        "constraints": {},
        "missing_fields": [],
        "needs_clarification": False,
        "product_id": "clothing-05",
        "cart_quantity": None,
        "cart_quantity_mode": None,
    }
    result = asyncio.run(
        interpret_message(
            ScriptedLLMClient([[LLMChunk(text=json.dumps(payload))]]),
            message,
            storefront=load_storefront_definition(),
            resolved_state={
                "_previous_suggestions": [
                    {"id": "clothing-04", "name": "قميص قطن"},
                    {"id": "clothing-05", "name": "قميص رسمي"},
                ]
            },
            pending_clarification=None,
        )
    )
    assert result.product_id == "clothing-05"
    assert not result.needs_clarification


@pytest.mark.parametrize(
    "bad_output",
    [
        "not json",
        "{}",
        '["not an intent"]',
        json.dumps(
            {
                "v": 7,
                "language": "en",
                "dialect": "english",
                "intent": "mutate",
                "constraints": {},
                "mutation_kind": "clear_cart",
                "mutation_source": "Open my cart",
                "missing_fields": [],
                "needs_clarification": False,
            }
        ),
    ],
)
def test_unusable_interpretation_asks_without_action_and_accepts_a_fresh_request(bad_output):
    client = real_client(
        [
            [LLMChunk(text=bad_output)],
            [LLMChunk(text=intent_payload(category="shoes"))],
        ]
    )

    session = client.post("/sessions").json()["session_id"]
    submitted = client.post(
        f"/sessions/{session}/messages",
        json={
            "text": "Open my cart",
            "snapshot": home_snapshot(),
        },
    )
    task_id = submitted.json()["task_id"]
    state = client.get(f"/sessions/{session}/state?tab_id=tab-local").json()
    assert state["task"]["status"] == "awaiting_answer"
    question = state["task"]["pending_question"]
    assert question["type"] == "ask_shopper"
    assert question["options"] == []
    assert not any(
        e["event"] == "error"
        for e in parse_sse(client.get(f"/sessions/{session}/events?once=true").text)
    )
    answer = client.post(
        f"/sessions/{session}/tasks/{task_id}/answers",
        json={
            "question_id": question["action_id"],
            "text": "عايز حذاء",
            "snapshot": home_snapshot(),
        },
    )
    assert answer.status_code == 202
    events = parse_sse(client.get(f"/sessions/{session}/events?once=true").text)
    actions = [e["data"]["action"] for e in events if e["event"] == "action"]
    assert [a["type"] for a in actions] == ["ask_shopper", "navigate"]
    assert actions[-1]["url"] == "/c/shoes"
    # The old question never authorizes a second action.
    assert (
        client.post(
            f"/sessions/{session}/tasks/{task_id}/answers",
            json={
                "question_id": question["action_id"],
                "text": "عايز حذاء",
                "snapshot": home_snapshot(),
            },
        ).status_code
        == 409
    )


def test_ambiguous_verified_product_choice_survives_refresh_without_another_model_call():
    store = SessionStore()
    session = store.create()
    snap = Snapshot.model_validate(home_snapshot())
    task = store.begin_interpretation(session.session_id, "افتح صفحته", snap)
    task.resolved_state["_previous_suggestions"] = [
        {"id": "clothing-04", "name": "قميص قطن"},
        {"id": "clothing-05", "name": "قميص رسمي"},
    ]
    intent = StructuredIntent.model_validate(
        {
            "v": 7,
            "language": "ar",
            "dialect": "egyptian_arabic",
            "intent": "open_product",
            "constraints": {},
            "product_id": None,
            "missing_fields": ["product_id"],
            "needs_clarification": True,
        }
    )
    store.finish_interpretation(session.session_id, task.task_id, task.model_call_id, intent)
    question = store.state(session.session_id, "tab-local")["task"]["pending_question"]
    assert question["options"] == ["قميص قطن", "قميص رسمي"]
    store.begin_answer_interpretation(
        session.session_id,
        task.task_id,
        question["action_id"],
        "قميص رسمي",
        snap,
        None,
    )
    assert task.model_call_id is None
    assert task.action.type == "navigate"
    assert task.action.url == "/p/clothing-05"
    assert task.action.sequence_number == question["sequence_number"] + 1


@pytest.mark.parametrize(
    "message",
    [
        "Don't open the Formal Shirt page",
        "افتح صفحة منتج تاني",
        "ماتفتحش صفحة القميص الرسمي",
        "Don’t open the Formal Shirt page",
        "Where is the Formal Shirt page?",
        "مَتفتحش صفحة القميص الرسمي",
    ],
)
def test_single_suggestion_does_not_authorize_an_unrelated_or_negated_page_request(message):
    payload = {
        "v": 7,
        "language": "ar",
        "dialect": "unknown",
        "intent": "open_product",
        "constraints": {},
        "product_id": "clothing-05",
        "missing_fields": [],
        "needs_clarification": False,
    }
    result = asyncio.run(
        interpret_message(
            ScriptedLLMClient([[LLMChunk(text=json.dumps(payload))]]),
            message,
            storefront=load_storefront_definition(),
            resolved_state={
                "_previous_suggestions": [
                    {
                        "id": "clothing-05",
                        "name": "Formal Shirt" if "Formal" in message else "قميص رسمي",
                    },
                ]
            },
            pending_clarification=None,
        )
    )
    assert result.needs_clarification
    assert result.product_id is None


def test_repeated_invalid_drafts_end_with_working_stop_instead_of_an_unanswerable_question():
    client = real_client([[LLMChunk(text="not json")]] * 2)
    session = client.post("/sessions").json()["session_id"]
    task = client.post(
        f"/sessions/{session}/messages",
        json={
            "text": "عايز حذاء",
            "snapshot": home_snapshot(),
        },
    ).json()["task_id"]
    for attempt in range(2):
        state = client.get(f"/sessions/{session}/state?tab_id=tab-local").json()
        question = state["task"]["pending_question"]
        if attempt < 1:
            assert question["options"] == []
            text = "عايز حذاء"
        else:
            assert question["options"] == ["إيقاف"]
            text = "إيقاف"
        response = client.post(
            f"/sessions/{session}/tasks/{task}/answers",
            json={
                "question_id": question["action_id"],
                "text": text,
                "snapshot": home_snapshot(),
            },
        )
        assert response.status_code == 202
    assert (
        client.get(f"/sessions/{session}/state?tab_id=tab-local").json()["task"]["status"]
        == "cancelled"
    )
