from fastapi.testclient import TestClient

from agent.app import create_app
from agent.sessions import SessionStore
from agent.tests.test_step import home_snapshot


def create_owned_session(client: TestClient, tab_id: str = "tab-1") -> str:
    response = client.post("/sessions", json={"tab_id": tab_id})
    assert response.status_code == 201
    return response.json()["session_id"]


def test_refresh_state_restores_conversation_and_requires_fresh_reconciliation() -> None:
    client = TestClient(create_app())
    session_id = create_owned_session(client)
    client.post(
        f"/sessions/{session_id}/messages",
        headers={"x-tab-id": "tab-1"},
        json={"text": "Show me running shoes under 2000 EGP", "snapshot": home_snapshot()},
    )

    restored = client.get(f"/sessions/{session_id}/state?tab_id=tab-1")

    assert restored.status_code == 200
    state = restored.json()
    assert state["lease"] == "owned"
    assert state["requires_reconciliation"] is True
    assert state["conversation"][0] == {
        "role": "shopper",
        "text": "Show me running shoes under 2000 EGP",
    }
    assert state["task"]["status"] == "awaiting_action_result"

    reconciled = client.post(
        f"/sessions/{session_id}/reconcile",
        headers={"x-tab-id": "tab-1"},
        json={"snapshot": home_snapshot()},
    )

    assert reconciled.status_code == 200
    reconciled_state = reconciled.json()
    assert reconciled_state["requires_reconciliation"] is False
    assert reconciled_state["task"]["status"] == "awaiting_answer"
    assert reconciled_state["task"]["pending_question"]["type"] == "ask_shopper"


def test_second_tab_requires_explicit_takeover_before_actions_resume() -> None:
    client = TestClient(create_app())
    session_id = create_owned_session(client)

    other_tab = client.get(f"/sessions/{session_id}/state?tab_id=tab-2")
    blocked_message = client.post(
        f"/sessions/{session_id}/messages",
        headers={"x-tab-id": "tab-2"},
        json={"text": "Show me running shoes under 2000 EGP", "snapshot": home_snapshot()},
    )
    takeover = client.post(
        f"/sessions/{session_id}/takeover",
        json={"tab_id": "tab-2"},
    )
    accepted_message = client.post(
        f"/sessions/{session_id}/messages",
        headers={"x-tab-id": "tab-2"},
        json={"text": "Show me running shoes under 2000 EGP", "snapshot": home_snapshot()},
    )

    assert other_tab.status_code == 200
    assert other_tab.json()["lease"] == "takeover_required"
    assert blocked_message.status_code == 409
    assert takeover.status_code == 200
    assert accepted_message.status_code == 202


def test_action_events_are_delivered_only_to_the_execution_lease_owner() -> None:
    client = TestClient(create_app())
    session_id = create_owned_session(client)
    client.post(
        f"/sessions/{session_id}/messages",
        headers={"x-tab-id": "tab-1"},
        json={"text": "Show me running shoes under 2000 EGP", "snapshot": home_snapshot()},
    )
    client.post(f"/sessions/{session_id}/takeover", json={"tab_id": "tab-2"})

    previous_owner = client.get(
        f"/sessions/{session_id}/events?after=0&once=true&tab_id=tab-1"
    ).text
    current_owner = client.get(f"/sessions/{session_id}/events?after=0&once=true&tab_id=tab-2").text

    assert "event: action" not in previous_owner
    assert "event: action" in current_owner


def test_inactive_session_expires_after_thirty_minutes() -> None:
    now = [1_000.0]
    store = SessionStore(clock=lambda: now[0])
    client = TestClient(create_app(store))
    session_id = create_owned_session(client)

    now[0] += 1_801
    expired = client.get(f"/sessions/{session_id}/state?tab_id=tab-1")

    assert expired.status_code == 410
    assert expired.json()["detail"] == "Session expired"
