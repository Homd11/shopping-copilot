from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from agent.planner import ActionIdentity, Language, ScriptedPlanner, detect_language
from agent.schemas import Action, ActionResult, Snapshot, to_wire

EventType = Literal["task_started", "narration", "action", "done", "cancelled", "error"]


@dataclass(frozen=True)
class SessionEvent:
    id: int
    event: EventType
    data: dict[str, Any]


@dataclass
class ActiveTask:
    task_id: str
    action: Action
    language: Language


@dataclass(frozen=True)
class AcceptedResult:
    task: ActiveTask
    result: ActionResult


@dataclass
class Session:
    session_id: str
    events: list[SessionEvent] = field(default_factory=list)
    active_task: ActiveTask | None = None
    accepted_results: dict[tuple[str, str, int], AcceptedResult] = field(default_factory=dict)


class SessionNotFound(KeyError):
    pass


class TaskConflict(ValueError):
    pass


class ActionResultMismatch(ValueError):
    pass


class SessionStore:
    def __init__(self, planner: ScriptedPlanner | None = None) -> None:
        self._planner = planner or ScriptedPlanner()
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session(session_id=f"session-{uuid4().hex}")
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFound(session_id) from error

    def submit_message(self, session_id: str, text: str, snapshot: Snapshot) -> ActiveTask:
        session = self.get(session_id)
        if session.active_task is not None:
            raise TaskConflict("A Shopping Task is already active")
        task_id = f"task-{uuid4().hex}"
        action = self._planner.plan(
            text,
            snapshot,
            ActionIdentity(
                task_id=task_id,
                action_id=f"action-{uuid4().hex}",
                sequence_number=1,
            ),
        )
        task = ActiveTask(task_id=task_id, action=action, language=detect_language(text))
        session.active_task = task
        self._append(session, "task_started", {"task_id": task_id})
        self._append(
            session,
            "narration",
            {"task_id": task_id, "text": action.narration},
        )
        self._append(
            session,
            "action",
            {"task_id": task_id, "action": to_wire(action)},
        )
        return task

    def accept_result(self, session_id: str, action_result: ActionResult) -> ActiveTask:
        session = self.get(session_id)
        result_identity = (
            action_result.task_id,
            action_result.action_id,
            action_result.sequence_number,
        )
        accepted = session.accepted_results.get(result_identity)
        if accepted is not None:
            if accepted.result != action_result:
                raise ActionResultMismatch("Action Result conflicts with the accepted result")
            return accepted.task
        task = session.active_task
        if task is None:
            raise ActionResultMismatch("There is no pending Action")
        action = task.action
        identity_matches = (
            action_result.task_id == task.task_id
            and action_result.action_id == action.action_id
            and action_result.sequence_number == action.sequence_number
        )
        if not identity_matches:
            raise ActionResultMismatch("Action Result does not match the pending Action")
        if action_result.status not in {"ok", "navigated"}:
            message = (
                "تعذر تنفيذ الإجراء بأمان. جرّب طلبًا آخر."
                if task.language == "ar"
                else "The action could not be completed safely. Try another request."
            )
            self._append(
                session,
                "error",
                {"task_id": task.task_id, "message": message},
            )
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            session.active_task = None
            return task
        narration = (
            "تم تطبيق الفلاتر بنجاح."
            if task.language == "ar"
            else "The filters were applied successfully."
        )
        summary = (
            "تم عرض أحذية الجري المناسبة للميزانية."
            if task.language == "ar"
            else "Running shoes within your budget are now shown."
        )
        self._append(
            session,
            "narration",
            {"task_id": task.task_id, "text": narration},
        )
        self._append(
            session,
            "done",
            {"task_id": task.task_id, "summary": summary, "language": task.language},
        )
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        session.active_task = None
        return task

    def stop(self, session_id: str) -> ActiveTask:
        session = self.get(session_id)
        task = session.active_task
        if task is None:
            raise TaskConflict("There is no active Shopping Task")
        session.active_task = None
        self._append(session, "cancelled", {"task_id": task.task_id})
        return task

    def events_after(self, session_id: str, event_id: int) -> list[SessionEvent]:
        return [event for event in self.get(session_id).events if event.id > event_id]

    @staticmethod
    def _append(session: Session, event: EventType, data: dict[str, Any]) -> None:
        payload = {"session_id": session.session_id, **data}
        session.events.append(SessionEvent(id=len(session.events) + 1, event=event, data=payload))
