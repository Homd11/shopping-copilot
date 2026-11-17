"""Structured event records that can never carry what the Shopper typed.

Every record is one JSON object. Each event has a fixed allow-list of fields, and
every value must be a number, a boolean, a value from a fixed set, or a short
token (ids, route templates, type names). Free text is rejected, so a later change
cannot leak Shopper words into the log by accident.
"""

import json
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

TOKEN = re.compile(r"[A-Za-z0-9_.:/{}\-]{1,200}")


def _token(value):
    return isinstance(value, str) and TOKEN.fullmatch(value) is not None


def _int(value):
    return isinstance(value, int) and not isinstance(value, bool)


EVENTS: dict[str, dict[str, Callable[[Any], bool]]] = {
    "http_request": {
        "method": lambda v: v in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"},
        "route": _token,
        "status": _int,
        "duration_ms": lambda v: _int(v) and v >= 0,
        "session_id": _token,
    },
}


class MemorySink:
    """Keeps records in memory; for tests."""

    def __init__(self):
        self.records: list[dict[str, Any]] = []

    def write(self, record: dict[str, Any]) -> None:
        self.records.append(record)


class StreamSink:
    """Writes one JSON line per record to a text stream (the terminal by default)."""

    def __init__(self, stream=None):
        self.stream = stream

    def write(self, record: dict[str, Any]) -> None:
        stream = self.stream if self.stream is not None else sys.stderr
        stream.write(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n")
        stream.flush()


class EventLog:
    def __init__(self, sink, *, release: str = "local"):
        if not _token(release):
            raise ValueError("Release id must be a token")
        self.sink = sink
        self.release = release
        self.failures = 0

    def emit(self, event: str, **fields: Any) -> None:
        allowed = EVENTS.get(event)
        if allowed is None:
            raise ValueError(f"Unknown event: {event}")
        for name, value in fields.items():
            check = allowed.get(name)
            if check is None:
                raise ValueError(f"Field {name} is not allowed on {event}")
            if value is not None and not check(value):
                raise ValueError(f"Field {name} on {event} is not an allowed value")
        record = {
            "time": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "release": self.release,
            "event": event,
            **{name: value for name, value in fields.items() if value is not None},
        }
        try:
            self.sink.write(record)
        except Exception:
            # Logging must never fail or slow the request it describes.
            self.failures += 1


# Fixed paths the Shopper middleware answers itself, before routing.
_FIXED_PATHS = frozenset(
    {"/shopper/bootstrap", "/shopper/challenge", "/shopper/link", "/shopper/admission"}
)
# Liveness and keep-alive traffic that would bury the useful records.
_NOISE = frozenset({"/health", "/shopper/activity"})


class RequestLog:
    """ASGI middleware recording one http_request per completed request."""

    def __init__(self, app, events: EventLog):
        self.app = app
        self.events = events

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] in _NOISE or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return
        status = 500
        started = time.monotonic()

        async def capture(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture)
        finally:
            route = scope.get("route")
            template = getattr(route, "path", None)
            if template is None:
                template = scope["path"] if scope["path"] in _FIXED_PATHS else "unmatched"
            session_id = scope.get("path_params", {}).get("session_id")
            self.events.emit(
                "http_request",
                method=scope["method"],
                route=template,
                status=status,
                duration_ms=int((time.monotonic() - started) * 1000),
                session_id=session_id if _token(session_id) else None,
            )
