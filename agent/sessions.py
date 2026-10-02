"""Stable session interface composing storage and Shopping Task modules."""

from collections.abc import Callable
from time import monotonic
from typing import Any

from agent import task_commands, task_interpretation, task_recovery, task_results
from agent.catalogue import DiscoveryResult
from agent.llm.intent import StructuredIntent
from agent.planner import ScriptedPlanner
from agent.schemas import ActionResult, Snapshot
from agent.session_registry import SESSION_TTL_SECONDS, SessionRegistry
from agent.session_state import (
    AcceptedResult,
    ActionResultMismatch,
    ActiveTask,
    EventType,
    InterpretationPauseReason,
    LeaseConflict,
    Session,
    SessionEvent,
    SessionExpired,
    SessionNotFound,
    TaskConflict,
    TaskStatus,
)
from agent.task_runtime import TaskRuntime

__all__ = [
    "SessionStore",
    "SESSION_TTL_SECONDS",
    "EventType",
    "TaskStatus",
    "InterpretationPauseReason",
    "SessionEvent",
    "ActiveTask",
    "AcceptedResult",
    "Session",
    "SessionNotFound",
    "SessionExpired",
    "TaskConflict",
    "ActionResultMismatch",
    "LeaseConflict",
]


class SessionStore:
    def __init__(
        self,
        planner: ScriptedPlanner | None = None,
        *,
        clock: Any = monotonic,
        confirmation_registrar: Callable[[str, str, str, str, int], bool] | None = None,
    ) -> None:
        self._registry = SessionRegistry(clock=clock)
        self._runtime = TaskRuntime(
            self._registry, planner or ScriptedPlanner(), clock, confirmation_registrar
        )

    def create(self, tab_id: str | None = None) -> Session:
        return self._registry.create(tab_id)

    def get(self, session_id: str) -> Session:
        return self._registry.get(session_id)

    def assert_lease(self, session: Session, tab_id: str | None) -> None:
        return self._registry.assert_lease(session, tab_id)

    def takeover(self, session_id: str, tab_id: str) -> Session:
        return self._registry.takeover(session_id, tab_id)

    def owns_lease(self, session_id: str, tab_id: str | None) -> bool:
        return self._registry.owns_lease(session_id, tab_id)

    def begin_interpretation(
        self,
        session_id: str,
        text: str,
        snapshot: Snapshot,
        *,
        replace_active: bool = False,
        tab_id: str | None = None,
    ) -> ActiveTask:
        return task_interpretation.begin_interpretation(
            self._runtime, session_id, text, snapshot, replace_active=replace_active, tab_id=tab_id
        )

    def finish_interpretation(
        self,
        session_id: str,
        task_id: str,
        call_id: str,
        intent: StructuredIntent,
    ) -> ActiveTask | None:
        return task_interpretation.finish_interpretation(
            self._runtime, session_id, task_id, call_id, intent
        )

    def finish_catalogue_interpretation(
        self,
        session_id: str,
        task_id: str,
        call_id: str,
        intent: StructuredIntent,
        result: DiscoveryResult,
        *,
        advice_text: str | None = None,
    ) -> ActiveTask | None:
        return task_interpretation.finish_catalogue_interpretation(
            self._runtime, session_id, task_id, call_id, intent, result, advice_text=advice_text
        )

    def begin_answer_interpretation(
        self,
        session_id: str,
        task_id: str,
        question_id: str,
        text: str,
        snapshot: Snapshot,
        tab_id: str | None,
    ) -> ActiveTask:
        return task_interpretation.begin_answer_interpretation(
            self._runtime, session_id, task_id, question_id, text, snapshot, tab_id
        )

    def fail_interpretation(
        self,
        session_id: str,
        task_id: str,
        call_id: str,
        reason: InterpretationPauseReason,
        *,
        retry_after_seconds: int | None = None,
    ) -> None:
        return task_interpretation.fail_interpretation(
            self._runtime,
            session_id,
            task_id,
            call_id,
            reason,
            retry_after_seconds=retry_after_seconds,
        )

    def retry_interpretation(
        self, session_id: str, task_id: str, tab_id: str | None, snapshot: Snapshot
    ) -> ActiveTask:
        return task_interpretation.retry_interpretation(
            self._runtime, session_id, task_id, tab_id, snapshot
        )

    def submit_message(
        self,
        session_id: str,
        text: str,
        snapshot: Snapshot,
        *,
        replace_active: bool = False,
        tab_id: str | None = None,
    ) -> ActiveTask:
        return task_commands.submit_message(
            self._runtime, session_id, text, snapshot, replace_active=replace_active, tab_id=tab_id
        )

    def answer(
        self,
        session_id: str,
        task_id: str,
        question_id: str,
        text: str,
        snapshot: Snapshot,
        tab_id: str | None = None,
    ) -> ActiveTask:
        return task_commands.answer(
            self._runtime, session_id, task_id, question_id, text, snapshot, tab_id
        )

    def is_auth_handoff(self, session_id: str, task_id: str, question_id: str) -> bool:
        return task_commands.is_auth_handoff(self._runtime, session_id, task_id, question_id)

    def is_guarded_confirmation(self, session_id: str, task_id: str, question_id: str) -> bool:
        return task_commands.is_guarded_confirmation(
            self._runtime, session_id, task_id, question_id
        )

    def is_stop_only_question(self, session_id: str, task_id: str, question_id: str) -> bool:
        return task_commands.is_stop_only_question(self._runtime, session_id, task_id, question_id)

    def accept_result(
        self, session_id: str, action_result: ActionResult, tab_id: str | None = None
    ) -> ActiveTask:
        return task_results.accept_result(self._runtime, session_id, action_result, tab_id)

    def stop(self, session_id: str, tab_id: str | None = None) -> ActiveTask:
        return task_commands.stop(self._runtime, session_id, tab_id)

    def state(self, session_id: str, tab_id: str) -> dict[str, Any]:
        return task_recovery.state(self._runtime, session_id, tab_id)

    def reconcile(self, session_id: str, tab_id: str, snapshot: Snapshot) -> dict[str, Any]:
        return task_recovery.reconcile(self._runtime, session_id, tab_id, snapshot)

    def events_after(self, session_id: str, event_id: int) -> list[SessionEvent]:
        return [event for event in self.get(session_id).events if event.id > event_id]
