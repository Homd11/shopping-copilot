from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Literal
from uuid import uuid4

from agent.planner import ActionIdentity, Language, ScriptedPlanner, detect_language
from agent.schemas import Action, ActionResult, AskShopperAction, Snapshot, to_wire

EventType = Literal["task_started", "narration", "action", "done", "cancelled", "error"]
TaskStatus = Literal[
    "awaiting_action_result", "awaiting_answer", "completed", "cancelled", "paused"
]
SESSION_TTL_SECONDS = 30 * 60


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
    message: str
    step_count: int = 1
    status: TaskStatus = "awaiting_action_result"


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
    conversation: list[dict[str, str]] = field(default_factory=list)
    last_task: ActiveTask | None = None
    last_snapshot: Snapshot | None = None
    lease_tab_id: str | None = None
    last_activity_at: float = 0.0
    requires_reconciliation: bool = False


class SessionNotFound(KeyError):
    pass


class SessionExpired(SessionNotFound):
    pass


class TaskConflict(ValueError):
    pass


class ActionResultMismatch(ValueError):
    pass


class LeaseConflict(ValueError):
    pass


class SessionStore:
    def __init__(
        self,
        planner: ScriptedPlanner | None = None,
        *,
        clock: Any = monotonic,
    ) -> None:
        self._planner = planner or ScriptedPlanner()
        self._clock = clock
        self._sessions: dict[str, Session] = {}
        self._expired_ids: set[str] = set()

    def create(self, tab_id: str | None = None) -> Session:
        session = Session(
            session_id=f"session-{uuid4().hex}",
            lease_tab_id=tab_id,
            last_activity_at=self._clock(),
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        if session_id in self._expired_ids:
            raise SessionExpired(session_id)
        try:
            session = self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFound(session_id) from error
        if self._clock() - session.last_activity_at > SESSION_TTL_SECONDS:
            del self._sessions[session_id]
            self._expired_ids.add(session_id)
            raise SessionExpired(session_id)
        return session

    def _touch(self, session: Session) -> None:
        session.last_activity_at = self._clock()

    def assert_lease(self, session: Session, tab_id: str | None) -> None:
        if session.lease_tab_id is None:
            if tab_id is not None:
                session.lease_tab_id = tab_id
            return
        if tab_id != session.lease_tab_id:
            raise LeaseConflict("Another browser tab owns this Shopping Task")

    def takeover(self, session_id: str, tab_id: str) -> Session:
        session = self.get(session_id)
        session.lease_tab_id = tab_id
        self._touch(session)
        return session

    def owns_lease(self, session_id: str, tab_id: str | None) -> bool:
        session = self.get(session_id)
        return session.lease_tab_id is None or session.lease_tab_id == tab_id

    def submit_message(
        self,
        session_id: str,
        text: str,
        snapshot: Snapshot,
        *,
        replace_active: bool = False,
        tab_id: str | None = None,
    ) -> ActiveTask:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        if session.active_task is not None:
            if not replace_active:
                raise TaskConflict("A Shopping Task is already active")
            replaced = session.active_task
            session.active_task = None
            self._append(session, "cancelled", {"task_id": replaced.task_id})
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
        task = ActiveTask(
            task_id=task_id,
            action=action,
            language=detect_language(text),
            message=text,
        )
        if isinstance(action, AskShopperAction):
            task.status = "awaiting_answer"
        session.active_task = task
        session.last_task = task
        session.last_snapshot = snapshot
        session.conversation.append({"role": "shopper", "text": text})
        session.conversation.append({"role": "copilot", "text": action.narration})
        self._touch(session)
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

    def answer(
        self,
        session_id: str,
        task_id: str,
        question_id: str,
        text: str,
        snapshot: Snapshot,
        tab_id: str | None = None,
    ) -> ActiveTask:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        task = session.active_task
        if (
            task is None
            or task.task_id != task_id
            or not isinstance(task.action, AskShopperAction)
            or task.action.action_id != question_id
        ):
            raise ActionResultMismatch("Answer does not match the pending Shopper question")
        if task.step_count >= 8:
            narration = (
                "وصلت للحد الأقصى للخطوات ووقفت المهمة مؤقتًا."
                if task.language == "ar"
                else "I reached the step limit and paused this task."
            )
            question = (
                "وصلنا لحد الخطوات. تحب نعمل إيه؟"
                if task.language == "ar"
                else "We reached the step limit. What would you like me to do?"
            )
            capped = AskShopperAction(
                v=1,
                type="ask_shopper",
                task_id=task.task_id,
                action_id=f"question-{uuid4().hex}",
                sequence_number=task.action.sequence_number + 1,
                narration=narration,
                question=question,
                options=["Start over", "Stop"]
                if task.language == "en"
                else ["ابدأ من جديد", "إيقاف"],
            )
            task.action = capped
            task.status = "awaiting_answer"
            self._append(session, "narration", {"task_id": task.task_id, "text": narration})
            self._append(session, "action", {"task_id": task.task_id, "action": to_wire(capped)})
            self._touch(session)
            return task
        action = self._planner.plan_answer(
            task.message,
            text,
            snapshot,
            ActionIdentity(
                task_id=task.task_id,
                action_id=f"action-{uuid4().hex}",
                sequence_number=task.action.sequence_number + 1,
            ),
        )
        task.action = action
        task.step_count += 1
        task.status = (
            "awaiting_answer" if isinstance(action, AskShopperAction) else "awaiting_action_result"
        )
        session.last_snapshot = snapshot
        session.conversation.append({"role": "shopper", "text": text})
        session.conversation.append({"role": "copilot", "text": action.narration})
        self._touch(session)
        self._append(session, "narration", {"task_id": task.task_id, "text": action.narration})
        self._append(session, "action", {"task_id": task.task_id, "action": to_wire(action)})
        return task

    def accept_result(
        self, session_id: str, action_result: ActionResult, tab_id: str | None = None
    ) -> ActiveTask:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
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
            question = (
                "تعذر الإجراء. ماذا تريد أن أفعل الآن؟"
                if task.language == "ar"
                else "The action did not work. What would you like me to do?"
            )
            narration = (
                "تعذر تنفيذ الإجراء بأمان."
                if task.language == "ar"
                else "The action could not be completed safely."
            )
            next_action = AskShopperAction(
                v=1,
                type="ask_shopper",
                task_id=task.task_id,
                action_id=f"question-{uuid4().hex}",
                sequence_number=action.sequence_number + 1,
                narration=narration,
                question=question,
                options=["Try again", "Stop"] if task.language == "en" else ["حاول تاني", "إيقاف"],
            )
            self._append(
                session,
                "narration",
                {"task_id": task.task_id, "text": narration},
            )
            self._append(
                session,
                "action",
                {"task_id": task.task_id, "action": to_wire(next_action)},
            )
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            task.action = next_action
            task.step_count += 1
            task.status = "awaiting_answer"
            session.last_snapshot = action_result.snapshot
            session.conversation.append({"role": "copilot", "text": narration})
            self._touch(session)
            return task
        narration = (
            "تم تطبيق الفلاتر بنجاح."
            if task.language == "ar"
            else "The filters were applied successfully."
        )
        normalized_message = task.message.lower()
        is_running_shoes = any(
            term in normalized_message for term in ("running", "جري", "للجري")
        ) and any(term in normalized_message for term in ("shoe", "كوتشي", "حذاء", "أحذية"))
        if is_running_shoes:
            summary = (
                "تم عرض أحذية الجري المناسبة للميزانية."
                if task.language == "ar"
                else "Running shoes within your budget are now shown."
            )
        else:
            summary = (
                "تم عرض المنتجات المطابقة."
                if task.language == "ar"
                else "Matching products are now shown."
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
        task.status = "completed"
        session.last_task = task
        session.last_snapshot = action_result.snapshot
        session.conversation.append({"role": "copilot", "text": summary})
        session.active_task = None
        self._touch(session)
        return task

    def stop(self, session_id: str, tab_id: str | None = None) -> ActiveTask:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        task = session.active_task
        if task is None:
            raise TaskConflict("There is no active Shopping Task")
        task.status = "cancelled"
        session.last_task = task
        session.active_task = None
        self._append(session, "cancelled", {"task_id": task.task_id})
        self._touch(session)
        return task

    def state(self, session_id: str, tab_id: str) -> dict[str, Any]:
        session = self.get(session_id)
        owned = session.lease_tab_id in {None, tab_id}
        if owned and session.active_task is not None:
            session.requires_reconciliation = True
        task = session.active_task or session.last_task
        pending_question = None
        if task is not None and isinstance(task.action, AskShopperAction):
            pending_question = to_wire(task.action)
        self._touch(session)
        return {
            "session_id": session.session_id,
            "lease": "owned" if owned else "takeover_required",
            "event_cursor": len(session.events),
            "conversation": session.conversation,
            "requires_reconciliation": session.requires_reconciliation,
            "task": (
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "pending_question": pending_question,
                }
                if task is not None
                else None
            ),
        }

    def reconcile(self, session_id: str, tab_id: str, snapshot: Snapshot) -> dict[str, Any]:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        task = session.active_task
        if (
            session.requires_reconciliation
            and task is not None
            and not isinstance(task.action, AskShopperAction)
        ):
            narration = (
                "بعد التحديث مش متأكد إذا الإجراء السابق اكتمل. مش هكرره تلقائيًا."
                if task.language == "ar"
                else (
                    "After refresh, I can't prove the previous action completed, "
                    "so I won't replay it."
                )
            )
            question = (
                "نكمل من الصفحة الحالية ولا نوقف المهمة؟"
                if task.language == "ar"
                else "Continue from the current page or stop this task?"
            )
            uncertain = AskShopperAction(
                v=1,
                type="ask_shopper",
                task_id=task.task_id,
                action_id=f"question-{uuid4().hex}",
                sequence_number=task.action.sequence_number + 1,
                narration=narration,
                question=question,
                options=["Continue", "Stop"] if task.language == "en" else ["كمّل", "إيقاف"],
            )
            task.action = uncertain
            task.status = "awaiting_answer"
            task.step_count += 1
            self._append(session, "narration", {"task_id": task.task_id, "text": narration})
            self._append(session, "action", {"task_id": task.task_id, "action": to_wire(uncertain)})
            session.conversation.append({"role": "copilot", "text": narration})
        session.last_snapshot = snapshot
        session.requires_reconciliation = False
        self._touch(session)
        view = self.state(session_id, tab_id)
        session.requires_reconciliation = False
        view["requires_reconciliation"] = False
        return view

    def events_after(self, session_id: str, event_id: int) -> list[SessionEvent]:
        return [event for event in self.get(session_id).events if event.id > event_id]

    @staticmethod
    def _append(session: Session, event: EventType, data: dict[str, Any]) -> None:
        payload = {"session_id": session.session_id, **data}
        session.events.append(SessionEvent(id=len(session.events) + 1, event=event, data=payload))
