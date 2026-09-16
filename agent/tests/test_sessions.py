import json

from fastapi.testclient import TestClient

from agent.app import create_app
from agent.tests.test_step import home_snapshot


def parse_sse(payload: str) -> list[dict[str, object]]:
    events = []
    for block in payload.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append(
            {
                "id": int(fields["id"]),
                "event": fields["event"],
                "data": json.loads(fields["data"]),
            }
        )
    return events


def test_session_streams_task_narration_and_action_in_order() -> None:
    client = TestClient(create_app())
    session_id = client.post("/sessions").json()["session_id"]

    submitted = client.post(
        f"/sessions/{session_id}/messages",
        json={
            "text": "عاوز كوتشي للجري بأقل من ٢٠٠٠",
            "snapshot": home_snapshot(),
        },
    )

    assert submitted.status_code == 202
    task_id = submitted.json()["task_id"]
    events = parse_sse(client.get(f"/sessions/{session_id}/events?after=0&once=true").text)
    assert [event["event"] for event in events] == ["task_started", "narration", "action"]
    assert [event["id"] for event in events] == [1, 2, 3]
    assert all(event["data"]["task_id"] == task_id for event in events)
    action = events[2]["data"]["action"]
    assert action["task_id"] == task_id
    assert action["action_id"]
    assert action["sequence_number"] == 1


def test_only_the_matching_action_result_completes_the_active_task() -> None:
    client = TestClient(create_app())
    session_id = client.post("/sessions").json()["session_id"]
    client.post(
        f"/sessions/{session_id}/messages",
        json={"text": "عاوز كوتشي للجري بأقل من ٢٠٠٠", "snapshot": home_snapshot()},
    )
    action_event = parse_sse(client.get(f"/sessions/{session_id}/events?after=0&once=true").text)[
        -1
    ]
    action = action_event["data"]["action"]
    filtered_snapshot = {
        **home_snapshot(),
        "url": "http://localhost:4000/c/shoes?type=running&max_price=2000",
        "title": "الأحذية",
    }
    result = {
        "v": 1,
        "task_id": action["task_id"],
        "action_id": action["action_id"],
        "sequence_number": action["sequence_number"],
        "status": "navigated",
        "snapshot": filtered_snapshot,
    }

    mismatch = client.post(
        f"/sessions/{session_id}/action-results",
        json={**result, "action_id": "different-action"},
    )
    accepted = client.post(f"/sessions/{session_id}/action-results", json=result)

    assert mismatch.status_code == 409
    assert accepted.status_code == 202
    completion = parse_sse(client.get(f"/sessions/{session_id}/events?after=3&once=true").text)
    assert [event["event"] for event in completion] == ["narration", "done"]
    assert completion[-1]["data"]["task_id"] == action["task_id"]


def test_duplicate_action_result_is_acknowledged_without_repeating_events() -> None:
    client = TestClient(create_app())
    session_id = client.post("/sessions").json()["session_id"]
    client.post(
        f"/sessions/{session_id}/messages",
        json={"text": "عاوز كوتشي للجري بأقل من ٢٠٠٠", "snapshot": home_snapshot()},
    )
    action = parse_sse(client.get(f"/sessions/{session_id}/events?after=0&once=true").text)[-1][
        "data"
    ]["action"]
    result = {
        "v": 1,
        "task_id": action["task_id"],
        "action_id": action["action_id"],
        "sequence_number": action["sequence_number"],
        "status": "navigated",
        "snapshot": {
            **home_snapshot(),
            "url": "http://localhost:4000/c/shoes?type=running&max_price=2000",
        },
    }

    first = client.post(f"/sessions/{session_id}/action-results", json=result)
    duplicate = client.post(f"/sessions/{session_id}/action-results", json=result)
    conflicting_duplicate = client.post(
        f"/sessions/{session_id}/action-results",
        json={**result, "status": "blocked"},
    )

    assert first.status_code == 202
    assert duplicate.status_code == 202
    assert conflicting_duplicate.status_code == 409
    assert duplicate.json() == {"task_id": action["task_id"], "status": "accepted"}
    completion = parse_sse(client.get(f"/sessions/{session_id}/events?after=3&once=true").text)
    assert [event["event"] for event in completion] == ["narration", "done"]


def test_stop_cancels_the_active_task_and_rejects_its_later_result() -> None:
    client = TestClient(create_app())
    session_id = client.post("/sessions").json()["session_id"]
    client.post(
        f"/sessions/{session_id}/messages",
        json={"text": "عاوز كوتشي للجري بأقل من ٢٠٠٠", "snapshot": home_snapshot()},
    )
    action = parse_sse(client.get(f"/sessions/{session_id}/events?after=0&once=true").text)[-1][
        "data"
    ]["action"]

    stopped = client.post(f"/sessions/{session_id}/stop")
    later_result = client.post(
        f"/sessions/{session_id}/action-results",
        json={
            "v": 1,
            "task_id": action["task_id"],
            "action_id": action["action_id"],
            "sequence_number": action["sequence_number"],
            "status": "navigated",
            "snapshot": home_snapshot(),
        },
    )

    assert stopped.status_code == 202
    assert later_result.status_code == 409
    events = parse_sse(client.get(f"/sessions/{session_id}/events?after=3&once=true").text)
    assert [event["event"] for event in events] == ["cancelled"]


def test_failed_action_result_reports_failure_without_completing_the_task() -> None:
    client = TestClient(create_app())
    session_id = client.post("/sessions").json()["session_id"]
    client.post(
        f"/sessions/{session_id}/messages",
        json={"text": "عاوز كوتشي للجري بأقل من ٢٠٠٠", "snapshot": home_snapshot()},
    )
    action = parse_sse(client.get(f"/sessions/{session_id}/events?after=0&once=true").text)[-1][
        "data"
    ]["action"]

    accepted = client.post(
        f"/sessions/{session_id}/action-results",
        json={
            "v": 1,
            "task_id": action["task_id"],
            "action_id": action["action_id"],
            "sequence_number": action["sequence_number"],
            "status": "blocked",
            "snapshot": home_snapshot(),
        },
    )

    assert accepted.status_code == 202
    events = parse_sse(client.get(f"/sessions/{session_id}/events?after=3&once=true").text)
    assert [event["event"] for event in events] == ["error"]
    assert events[0]["data"]["message"] == "تعذر تنفيذ الإجراء بأمان. جرّب طلبًا آخر."


def test_english_task_completion_remains_in_english() -> None:
    client = TestClient(create_app())
    session_id = client.post("/sessions").json()["session_id"]
    client.post(
        f"/sessions/{session_id}/messages",
        json={"text": "Show me running shoes under 2000 EGP", "snapshot": home_snapshot()},
    )
    action = parse_sse(client.get(f"/sessions/{session_id}/events?after=0&once=true").text)[-1][
        "data"
    ]["action"]
    client.post(
        f"/sessions/{session_id}/action-results",
        json={
            "v": 1,
            "task_id": action["task_id"],
            "action_id": action["action_id"],
            "sequence_number": action["sequence_number"],
            "status": "navigated",
            "snapshot": home_snapshot(),
        },
    )

    events = parse_sse(client.get(f"/sessions/{session_id}/events?after=3&once=true").text)
    assert [event["event"] for event in events] == ["narration", "done"]
    assert events[0]["data"]["text"] == "The filters were applied successfully."
    assert events[1]["data"]["summary"] == "Running shoes within your budget are now shown."
