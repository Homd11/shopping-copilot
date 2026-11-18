"""Structured event records that can never carry what the Shopper typed.

Every record is one JSON object. Each event has a fixed allow-list of fields, and
every value must be a number, a boolean, a value from a fixed set, or a short
token (ids, route templates, type names). Free text is rejected, so a later change
cannot leak Shopper words into the log by accident.
"""

import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, get_args

from starlette.routing import Match

from agent.llm.intent import Dialect, IntentName
from agent.schemas import Action, ActionResult
from agent.session_state import EventType, InterpretationPauseReason

TOKEN = re.compile(r"[A-Za-z0-9_.:/{}\-]{1,200}")
SESSION_ID = re.compile(r"session-[0-9a-f]{32}")
METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OTHER"})


def _token(value):
    return isinstance(value, str) and TOKEN.fullmatch(value) is not None


def _session_id(value):
    return isinstance(value, str) and SESSION_ID.fullmatch(value) is not None


def _int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_count(value) -> bool:
    return _int(value) and value >= 0


def is_cost(value) -> bool:
    """A finite, non-negative dollar amount."""
    number = isinstance(value, int | float) and not isinstance(value, bool)
    return number and math.isfinite(value) and value >= 0


TASK_ID = re.compile(r"task-[0-9a-f]{32}")
SHOPPER = re.compile(r"[0-9a-f]{16}")
INVITATION_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
TASK_EVENTS = frozenset(get_args(EventType))
ACTION_TYPES = frozenset(
    get_args(variant.model_fields["type"].annotation)[0]
    for variant in get_args(get_args(Action)[0])
)
INTENTS = frozenset(get_args(IntentName))
DIALECTS = frozenset(get_args(Dialect))
# Interpretation failures, plus pauses the task engine makes on its own.
PAUSE_REASONS = frozenset(get_args(InterpretationPauseReason)) | {
    "refresh",
    "cart_navigation_failed",
    "cart_edit_unavailable",
    "guarded_control_missing",
}
RESULT_STATUSES = frozenset(get_args(ActionResult.model_fields["status"].annotation))


def _matches(pattern):
    return lambda value: isinstance(value, str) and pattern.fullmatch(value) is not None


def _one_of(values):
    return lambda value: value in values


def shopper_tag(binding) -> str | None:
    """A short scrambled id that groups one Shopper's records without identifying them."""
    if binding is None:
        return None
    return hashlib.sha256(b"event-log:" + binding.context.encode()).hexdigest()[:16]


_SEQUENCE = is_count
_LANGUAGE = _one_of({"ar", "en"})

_TASK_CONTEXT = {
    "session_id": lambda v: _session_id(v),
    "task_id": _matches(TASK_ID),
    "shopper": _matches(SHOPPER),
    "invitation_id": _matches(INVITATION_ID),
}

EVENTS: dict[str, dict[str, Callable[[Any], bool]]] = {
    "task": {
        **_TASK_CONTEXT,
        "kind": _one_of(TASK_EVENTS),
        "action_type": _one_of(ACTION_TYPES),
        "sequence": _SEQUENCE,
        "question_kind": _one_of({"confirmation", "question"}),
        "language": _LANGUAGE,
    },
    "intent": {
        **_TASK_CONTEXT,
        "intent": _one_of(INTENTS),
        "language": _LANGUAGE,
        "dialect": _one_of(DIALECTS),
        "needs_clarification": lambda v: isinstance(v, bool),
    },
    "confirmation": {
        **_TASK_CONTEXT,
        "outcome": _one_of(
            {"consumed", "stopped", "stale", "expired", "unregistered", "invalidated"}
        ),
        "mutation_kind": _one_of({"clear_cart", "submit_checkout"}),
    },
    "model_call": {
        **_TASK_CONTEXT,
        "provider": _token,
        "model": _token,
        "prompt_version": _token,
        "schema_version": _SEQUENCE,
        "latency_ms": _SEQUENCE,
        "outcome": _one_of({"ok", "failed"}),
        "failure": _one_of(PAUSE_REASONS),
        "prompt_tokens": _SEQUENCE,
        "completion_tokens": _SEQUENCE,
        "cost_usd": is_cost,
        "attempt_id": _token,
    },
    "retrieval_turn": {
        **_TASK_CONTEXT,
        "outcome": _one_of({"recommend", "clarify", "execute", "exhausted", "failed"}),
        "decisions": _SEQUENCE,
        "reads": _SEQUENCE,
        "advice": _SEQUENCE,
    },
    "task_paused": {
        **_TASK_CONTEXT,
        "reason": _one_of(PAUSE_REASONS),
    },
    "action_result": {
        **_TASK_CONTEXT,
        "action_type": _one_of(ACTION_TYPES),
        "sequence": _SEQUENCE,
        "status": _one_of(RESULT_STATUSES),
    },
    "http_request": {
        "method": lambda v: v in METHODS,
        "route": _token,
        "status": _int,
        "duration_ms": lambda v: _int(v) and v >= 0,
        "session_id": _session_id,
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


class FileSink:
    """Appends records to a private, size-limited file that rotates through three names.

    Total size stays under three times ``maximum_bytes`` (about 5 MiB by default), and
    files untouched for seven days are removed. Any problem raises, and the event log
    counts it instead of failing the request it describes.
    """

    NAMES = ("events.jsonl", "events.jsonl.1", "events.jsonl.2")
    RETENTION_SECONDS = 7 * 24 * 3600

    def __init__(self, directory, *, maximum_bytes: int = 5 * 1024 * 1024 // 3):
        self.directory = Path(directory)
        self.maximum_bytes = maximum_bytes
        self._lock = threading.Lock()
        self._checked = False

    def write(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        encoded = (line + "\n").encode()
        if len(encoded) > self.maximum_bytes:
            raise ValueError("Record larger than the log file limit")
        with self._lock:
            if not self._checked:
                self._check_private()
                self._prune()
                self._checked = True
            current = self.directory / self.NAMES[0]
            size = current.stat().st_size if current.exists() else 0
            if size + len(encoded) > self.maximum_bytes:
                self._rotate()
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(current, flags, 0o600)
            try:
                os.write(descriptor, encoded)
            finally:
                os.close(descriptor)

    def _check_private(self) -> None:
        info = self.directory.stat()
        if os.name == "posix" and (info.st_uid != os.geteuid() or info.st_mode & 0o077):
            raise PermissionError("Event log directory must be private to the Agent")

    def _rotate(self) -> None:
        names = [self.directory / name for name in self.NAMES]
        names[-1].unlink(missing_ok=True)
        for older, newer in zip(reversed(names[:-1]), reversed(names[1:]), strict=True):
            if older.exists():
                older.replace(newer)
        self._prune()

    def _prune(self) -> None:
        cutoff = time.time() - self.RETENTION_SECONDS
        for name in self.NAMES:
            path = self.directory / name
            if path.exists() and path.stat().st_mtime < cutoff:
                path.unlink()


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

    def __init__(self, app, events: EventLog, routes=()):
        self.app = app
        self.events = events
        # Requests rejected before routing still name the endpoint they targeted.
        self.routes = routes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] in _NOISE or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return
        status = 499  # client went away before any response started
        started = time.monotonic()

        async def capture(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture)
        finally:
            try:
                template, params = self._route(scope)
                session_id = params.get("session_id")
                self.events.emit(
                    "http_request",
                    method=scope["method"] if scope["method"] in METHODS else "OTHER",
                    route=template if _token(template) else "unmatched",
                    status=status,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    session_id=session_id if _session_id(session_id) else None,
                )
            except Exception:
                # Logging must never fail or slow the request it describes.
                self.events.failures += 1

    def _route(self, scope):
        route = scope.get("route")
        if route is not None:
            return route.path, scope.get("path_params", {})
        if scope["path"] in _FIXED_PATHS:
            return scope["path"], {}
        for candidate in self.routes:
            match, child = candidate.matches(scope)
            if match is not Match.NONE:
                return candidate.path, child.get("path_params", {})
        return "unmatched", {}


# The session and task a piece of work belongs to, so records made deep inside a
# turn (model calls, retrieval) are tied to it without threading ids through.
_scope: ContextVar[tuple[EventLog, dict[str, Any]] | None] = ContextVar("event_scope", default=None)


@contextmanager
def bind(events: EventLog | None, **context: Any):
    token = _scope.set(None if events is None else (events, context))
    try:
        yield
    finally:
        _scope.reset(token)


def record(event: str, **fields: Any) -> None:
    """Emit a record in the current scope; a no-op outside one, never raises."""
    scope = _scope.get()
    if scope is None:
        return
    events, context = scope
    try:
        events.emit(event, **context, **fields)
    except Exception:
        events.failures += 1
