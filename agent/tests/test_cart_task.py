import pytest

from agent.llm.intent import StructuredIntent
from agent.schemas import ActionResult, AskShopperAction, Snapshot
from agent.sessions import SessionStore
from agent.tests.test_step import home_snapshot


def snapshot():
    return Snapshot.model_validate(
        {
            **home_snapshot(),
            "url": "http://localhost:4000/p/shoe-09",
            "elements": [
                {
                    "id": 1,
                    "role": "combobox",
                    "name": "المقاس",
                    "value": "43",
                    "options": ["43"],
                    "visible": True,
                },
                {
                    "id": 2,
                    "role": "combobox",
                    "name": "اللون",
                    "value": "blue",
                    "options": ["blue"],
                    "visible": True,
                },
                {"id": 3, "role": "textbox", "name": "الكمية", "value": "1", "visible": True},
                {
                    "id": 4,
                    "role": "button",
                    "name": "أضف إلى السلة",
                    "form_action": "/cart/items",
                    "visible": True,
                },
            ],
        }
    )


def intent(source="Add this to my cart"):
    return StructuredIntent.model_validate(
        {
            "v": 5,
            "language": "en",
            "dialect": "english",
            "intent": "cart_edit",
            "cart_operation": "add",
            "cart_source": source,
            "constraints": {},
            "missing_fields": [],
            "needs_clarification": False,
        }
    )


@pytest.mark.parametrize("confirmed", [True, False])
def test_cart_task_completes_only_after_storefront_confirmation(confirmed):
    store = SessionStore()
    session = store.create()
    task = store.begin_interpretation(session.session_id, "Add this to my cart", snapshot())
    store.finish_interpretation(session.session_id, task.task_id, task.model_call_id, intent())
    action = task.action
    assert action.type == "click"
    updated = snapshot().model_dump(by_alias=True, exclude_none=True)
    updated["elements"] += [
        {"id": 5, "role": "status", "name": "تمت الإضافة إلى السلة", "visible": True}
    ]
    result = ActionResult.model_validate(
        {
            "v": 1,
            "task_id": task.task_id,
            "action_id": action.action_id,
            "sequence_number": action.sequence_number,
            "status": "ok" if confirmed else "blocked",
            "snapshot": updated,
        }
    )
    store.accept_result(session.session_id, result)
    assert task.status == ("completed" if confirmed else "paused")


def test_missing_product_options_hands_back_without_add():
    store = SessionStore()
    session = store.create()
    current = snapshot()
    current.elements[0].value = ""
    task = store.begin_interpretation(session.session_id, "Add this to my cart", current)
    store.finish_interpretation(session.session_id, task.task_id, task.model_call_id, intent())
    assert isinstance(task.action, AskShopperAction)


def test_negated_cart_edit_cannot_become_an_action():
    store = SessionStore()
    session = store.create()
    task = store.begin_interpretation(session.session_id, "Do not add this to my cart", snapshot())
    with pytest.raises(ValueError):
        store.finish_interpretation(
            session.session_id, task.task_id, task.model_call_id, intent("add this to my cart")
        )


@pytest.mark.parametrize("constraints", [{"size": "44"}, {"color": "red"}])
def test_unsourced_cart_variant_is_rejected(constraints):
    from agent.cart import validate_cart_intent

    requested = intent().model_copy(
        update={"constraints": intent().constraints.model_copy(update=constraints)}
    )
    with pytest.raises(ValueError, match="variant"):
        validate_cart_intent("Add this to my cart", requested)
