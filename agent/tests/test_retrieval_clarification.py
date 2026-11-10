"""Clarification replies through the retrieval-enabled HTTP task lifecycle."""

import json

import pytest

from agent.app import create_app
from agent.llm import LLMChunk, LLMSettings
from agent.tests.http_client import TestClient
from agent.tests.test_cart_task import snapshot
from agent.tests.test_sessions import parse_sse


@pytest.mark.parametrize(
    "field,answer,canonical,options",
    [("color", "اسود", "black", ["gray", "black"]), ("size", "٤٢", "42", ["40", "42"])],
)
def test_retrieval_clarification_reply_selects_variant_and_completes_cart(
    field, answer, canonical, options
):
    class Model:
        def __init__(self):
            self.requests = []

        async def complete(self, request):
            self.requests.append(request)
            if request.prompt_version.startswith("catalogue-"):
                payload = {"kind": "execute"}
            else:
                latest = request.messages[-1].content
                payload = {
                    "v": 9,
                    "language": "ar",
                    "dialect": "egyptian_arabic",
                    "intent": "cart_edit",
                    "cart_operation": "add",
                    "product_id": "shoe-09",
                    "cart_target_id": 4,
                    "cart_source": latest,
                    "constraints": {field: canonical} if latest == answer else {},
                    "missing_fields": [],
                    "needs_clarification": False,
                }
            yield LLMChunk(text=json.dumps(payload, ensure_ascii=False))

    class Catalogue:
        async def search(self, query):
            pytest.fail("A pending cart option must not become a catalogue search")

        async def details(self, query):
            pytest.fail("Observed cart controls need no catalogue read")

    model = Model()
    app = create_app(
        llm_settings=LLMSettings(provider="groq", model="test"),
        llm_client=model,
        catalogue_client=Catalogue(),
        catalogue_retrieval_enabled=True,
    )
    current = snapshot().model_dump(mode="json", by_alias=True, exclude_none=True)
    control = current["elements"][1 if field == "color" else 0]
    control.update(value="", options=options)
    with TestClient(app) as client:
        sid = client.post("/sessions").json()["session_id"]
        assert (
            client.post(
                f"/sessions/{sid}/messages",
                json={
                    "text": "ضيف المنتج للسلة",
                    "snapshot": current,
                },
            ).status_code
            == 202
        )

        def events():
            return parse_sse(client.get(f"/sessions/{sid}/events?once=true").text)

        def last_action():
            return [e["data"]["action"] for e in events() if e["event"] == "action"][-1]

        question = last_action()
        assert question["type"] == "ask_shopper"
        assert (
            client.post(
                f"/sessions/{sid}/tasks/{question['task_id']}/answers",
                json={
                    "question_id": question["action_id"],
                    "text": answer,
                    "snapshot": current,
                },
            ).status_code
            == 202
        )
        request = model.requests[-1]
        context = json.loads(
            request.system.split("\n", 1)[0].removeprefix("Shopping Copilot intent context: ")
        )
        assert context["pending_clarification"] == question["question"]
        assert context["resolved_state"]["_intent"]["cart_operation"] == "add"
        assert context["resolved_state"]["_answers"][-1] == answer
        action = last_action()
        assert action["type"] == "select" and action["id"] == control["id"]
        assert action["option"] == canonical

        def report(action):
            assert (
                client.post(
                    f"/sessions/{sid}/action-results",
                    json={
                        "v": 1,
                        "task_id": action["task_id"],
                        "action_id": action["action_id"],
                        "sequence_number": action["sequence_number"],
                        "status": "ok",
                        "snapshot": current,
                    },
                ).status_code
                == 202
            )

        control["value"] = canonical
        report(action)
        action = last_action()
        assert action["type"] == "click" and action["id"] == 4
        current["elements"].append(
            {
                "id": 5,
                "role": "status",
                "name": "تمت الإضافة إلى السلة",
                "visible": True,
            }
        )
        report(action)
        assert events()[-1]["event"] == "done"
        assert not any(e["event"] == "error" for e in events())
