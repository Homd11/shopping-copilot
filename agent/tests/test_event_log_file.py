"""The host's private, bounded, rotating event log file (seam 2)."""

import json
import os
import time

import pytest

from agent.event_log import EventLog, FileSink


def lines(directory, name="events.jsonl"):
    path = directory / name
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_records_are_appended_as_one_json_line_each(tmp_path) -> None:
    log = EventLog(FileSink(tmp_path), release="abc123")

    log.emit("http_request", method="GET", route="/sessions", status=200, duration_ms=3)
    log.emit("http_request", method="POST", route="/sessions", status=201, duration_ms=4)

    written = lines(tmp_path)
    assert [(r["method"], r["status"], r["release"]) for r in written] == [
        ("GET", 200, "abc123"),
        ("POST", 201, "abc123"),
    ]


def test_the_log_rotates_and_never_grows_past_its_limit(tmp_path) -> None:
    sink = FileSink(tmp_path, maximum_bytes=2000)
    log = EventLog(sink)

    for status in range(200, 400):
        log.emit("http_request", method="GET", route="/sessions", status=status, duration_ms=1)

    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["events.jsonl", "events.jsonl.1", "events.jsonl.2"]
    assert all((tmp_path / n).stat().st_size <= 2000 for n in names)
    assert lines(tmp_path)[-1]["status"] == 399
    kept = [r["status"] for n in reversed(names) for r in lines(tmp_path, n)]
    assert kept == sorted(kept) and 200 not in kept


def test_files_older_than_seven_days_are_pruned(tmp_path) -> None:
    old = tmp_path / "events.jsonl.2"
    old.write_text('{"event":"http_request"}\n')
    stale = time.time() - 8 * 24 * 3600
    os.utime(old, (stale, stale))
    sink = FileSink(tmp_path, maximum_bytes=200)

    EventLog(sink).emit("http_request", method="GET", route="/sessions", status=200, duration_ms=1)

    assert not old.exists()


def test_a_write_failure_is_counted_and_never_raised(tmp_path) -> None:
    log = EventLog(FileSink(tmp_path / "missing" / "dir"))

    log.emit("http_request", method="GET", route="/sessions", status=200, duration_ms=1)

    assert log.failures == 1


@pytest.mark.skipif(os.name != "posix", reason="file modes are POSIX")
def test_the_log_is_private_to_the_agent_user(tmp_path) -> None:
    tmp_path.chmod(0o700)
    EventLog(FileSink(tmp_path)).emit(
        "http_request", method="GET", route="/sessions", status=200, duration_ms=1
    )
    assert (tmp_path / "events.jsonl").stat().st_mode & 0o777 == 0o600

    shared = tmp_path / "shared"
    shared.mkdir(mode=0o755)
    shared.chmod(0o755)
    log = EventLog(FileSink(shared))
    log.emit("http_request", method="GET", route="/sessions", status=200, duration_ms=1)
    assert log.failures == 1 and not (shared / "events.jsonl").exists()
