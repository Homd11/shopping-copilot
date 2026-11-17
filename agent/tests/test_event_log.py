"""Event log records observed through the Agent's HTTP API (seam 1)."""

import json

import pytest

from agent.app import create_app
from agent.event_log import EventLog, MemorySink
from agent.tests.http_client import TestClient
from agent.tests.test_step import home_snapshot


def records(sink, event):
    return [record for record in sink.records if record["event"] == event]


def test_each_request_is_recorded_with_its_route_template_status_and_duration() -> None:
    sink = MemorySink()
    client = TestClient(create_app(event_sink=sink))

    session_id = client.post("/sessions").json()["session_id"]
    client.get(f"/sessions/{session_id}/state?tab_id=tab-1")

    requests = records(sink, "http_request")
    state = [r for r in requests if r["route"] == "/sessions/{session_id}/state"]
    assert len(state) == 1
    assert state[0]["method"] == "GET"
    assert state[0]["status"] == 200
    assert isinstance(state[0]["duration_ms"], int) and state[0]["duration_ms"] >= 0
    assert all(session_id not in r["route"] for r in requests)


def test_health_checks_and_activity_pings_are_not_recorded() -> None:
    sink = MemorySink()
    client = TestClient(create_app(event_sink=sink))

    client.get("/health")
    client.post("/shopper/activity")

    routes = [r["route"] for r in records(sink, "http_request")]
    assert "/health" not in routes
    assert "/shopper/activity" not in routes


def test_what_the_shopper_typed_appears_in_no_record() -> None:
    sink = MemorySink()
    client = TestClient(create_app(event_sink=sink))
    session_id = client.post("/sessions").json()["session_id"]
    typed = "عاوز كوتشي للجري بأقل من ٢٠٠٠ secret-phrase-7731"

    submitted = client.post(
        f"/sessions/{session_id}/messages", json={"text": typed, "snapshot": home_snapshot()}
    )

    assert submitted.status_code == 202
    assert any(r["route"] == "/sessions/{session_id}/messages" for r in sink.records)
    dumped = json.dumps(sink.records, ensure_ascii=False)
    assert "secret-phrase-7731" not in dumped
    assert "كوتشي" not in dumped


def test_a_record_refuses_unknown_fields_and_free_text() -> None:
    log = EventLog(MemorySink())

    with pytest.raises(ValueError):
        log.emit("http_request", method="GET", message="hello")
    with pytest.raises(ValueError):
        log.emit("http_request", method="GET", route="عاوز كوتشي")
    with pytest.raises(ValueError):
        log.emit("http_request", method="GET", route="a sentence with spaces")
    with pytest.raises(ValueError):
        log.emit("no_such_event")
    assert log.sink.records == []


def test_without_a_sink_records_print_to_the_terminal_as_json_lines(capsys) -> None:
    client = TestClient(create_app())

    client.post("/sessions")

    lines = [line for line in capsys.readouterr().err.splitlines() if line.startswith("{")]
    parsed = [json.loads(line) for line in lines]
    assert any(r["event"] == "http_request" and r["route"] == "/sessions" for r in parsed)
    assert all(r["release"] == "local" for r in parsed)
