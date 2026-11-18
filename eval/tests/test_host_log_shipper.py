"""Shipping host event records to CloudWatch Logs (seam 3: a fake CloudWatch client)."""

import json

import pytest

GROUP = "/scpilot/agent-events"


class FakeLogs:
    """Records put_log_events calls; can be made unreachable or missing its stream."""

    class exceptions:
        class ResourceNotFoundException(Exception):
            pass

        class ResourceAlreadyExistsException(Exception):
            pass

    def __init__(self, *, streams=("agent-local",)):
        self.sent = []
        self.streams = set(streams)
        self.unreachable = False

    def create_log_stream(self, *, logGroupName, logStreamName):
        assert logGroupName == GROUP
        if logStreamName in self.streams:
            raise self.exceptions.ResourceAlreadyExistsException()
        self.streams.add(logStreamName)

    def put_log_events(self, *, logGroupName, logStreamName, logEvents):
        if self.unreachable:
            raise ConnectionError("CloudWatch unreachable")
        if logStreamName not in self.streams:
            raise self.exceptions.ResourceNotFoundException()
        assert logGroupName == GROUP
        assert [e["timestamp"] for e in logEvents] == sorted(e["timestamp"] for e in logEvents)
        self.sent.extend(json.loads(e["message"]) for e in logEvents)
        return {}


def line(status, *, debug=False, second=1):
    record = {
        "time": f"2026-11-18T10:00:{second:02d}.000+00:00",
        "release": "local",
        "event": "debug" if debug else "http_request",
        "status": status,
    }
    if debug:
        record.update(debug=True, kind="shopper_message", text="عايز كوتشي")
    return json.dumps(record, ensure_ascii=True) + "\n"


def append(folder, text, name="events.jsonl"):
    with open(folder / name, "a", encoding="ascii", newline="\n") as file:
        file.write(text)


@pytest.fixture
def folders(tmp_path):
    logs, state = tmp_path / "logs", tmp_path / "state"
    logs.mkdir()
    state.mkdir()
    return logs, state


def shipper(folders, client):
    from deploy.host_log_shipper import Shipper

    logs, state = folders
    return Shipper(logs, client, group=GROUP, stream="agent-local", checkpoint=state / "ship.json")


def statuses(client):
    return [r["status"] for r in client.sent]


def test_new_records_are_shipped_once_in_order(folders) -> None:
    client = FakeLogs()
    ship = shipper(folders, client)
    append(folders[0], line(200, second=1) + line(201, second=2))

    ship.poll()
    ship.poll()
    append(folders[0], line(202, second=3))
    ship.poll()

    assert statuses(client) == [200, 201, 202]


def test_debug_records_are_never_shipped(folders) -> None:
    client = FakeLogs()
    append(folders[0], line(200) + line(0, debug=True) + line(201))

    shipper(folders, client).poll()

    assert statuses(client) == [200, 201]
    assert "كوتشي" not in json.dumps(client.sent, ensure_ascii=False)


def test_nothing_is_lost_while_cloudwatch_is_unreachable(folders) -> None:
    client = FakeLogs()
    ship = shipper(folders, client)
    append(folders[0], line(200) + line(201))
    client.unreachable = True

    assert ship.poll() is False
    client.unreachable = False
    ship.poll()

    assert statuses(client) == [200, 201]


def test_after_a_restart_shipping_resumes_without_duplicates_or_gaps(folders) -> None:
    client = FakeLogs()
    append(folders[0], line(200) + line(201))
    shipper(folders, client).poll()
    append(folders[0], line(202))

    shipper(folders, client).poll()

    assert statuses(client) == [200, 201, 202]


def test_records_left_in_a_rotated_file_go_out_before_the_new_file(folders) -> None:
    logs, _ = folders
    client = FakeLogs()
    ship = shipper(folders, client)
    append(logs, line(200, second=1))
    ship.poll()
    append(logs, line(201, second=2))
    (logs / "events.jsonl").rename(logs / "events.jsonl.1")
    append(logs, line(202, second=3))

    ship.poll()

    assert statuses(client) == [200, 201, 202]


def test_a_half_written_line_waits_until_it_is_complete(folders) -> None:
    logs, _ = folders
    client = FakeLogs()
    ship = shipper(folders, client)
    whole = line(200)
    append(logs, line(199) + whole[:20])

    ship.poll()
    append(logs, whole[20:])
    ship.poll()

    assert statuses(client) == [199, 200]


def test_a_missing_stream_is_created_and_the_batch_sent(folders) -> None:
    client = FakeLogs(streams=())
    append(folders[0], line(200))

    shipper(folders, client).poll()

    assert "agent-local" in client.streams
    assert statuses(client) == [200]
