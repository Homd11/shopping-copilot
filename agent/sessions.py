import re
from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import uuid4

from agent.cart import MESSAGES, plan_cart_edit, scripted_cart_intent, validate_cart_intent
from agent.catalogue import DiscoveryResult
from agent.confirmation import (
    ConfirmationLedger,
    MutationProposal,
    classify_guarded_mutation,
    scripted_mutation_intent,
    validate_mutation_interpretation,
)
from agent.llm.intent import StructuredIntent
from agent.navigation import is_deictic_cart_open
from agent.planner import (
    ActionIdentity,
    Language,
    ScriptedPlanner,
    detect_language,
    is_expected_login_redirect,
    snapshot_matches_url,
)
from agent.schemas import (
    Action,
    ActionResult,
    AskShopperAction,
    GuardedClickAction,
    NavigateAction,
    Snapshot,
    SpotlightAction,
    to_wire,
)

EventType = Literal[
    "task_started", "narration", "action", "suggestions", "done", "cancelled", "error"
]
TaskStatus = Literal[
    "interpreting", "awaiting_action_result", "awaiting_answer", "completed", "cancelled", "paused"
]
InterpretationPauseReason = Literal[
    "throttled",
    "timeout",
    "network",
    "provider_http",
    "invalid_response",
    "catalogue_unavailable",
    "interrupted",
    "unexpected",
]
SESSION_TTL_SECONDS = 30 * 60
_CONTEXT_TEXT_LIMIT = 2000
_CONTEXT_ANSWER_LIMIT = 8


def _visible_product_count(snapshot: Snapshot) -> int | None:
    counts = {
        int(match.group(1))
        for element in snapshot.elements
        if element.visible and element.role == "heading" and element.level == 2
        if (match := re.fullmatch(r"(\d+) منتجات", element.name.strip())) is not None
    }
    return next(iter(counts)) if len(counts) == 1 else None


def _bounded_answers(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item[:_CONTEXT_TEXT_LIMIT] for item in value if isinstance(item, str)][
        -_CONTEXT_ANSWER_LIMIT:
    ]


def _intent_context(task: "ActiveTask", intent: StructuredIntent) -> dict[str, Any]:
    constraints = intent.constraints.model_dump(mode="json", exclude_none=True)
    original = task.resolved_state.get("_original_message", task.message)
    return {
        **constraints,
        "_intent": intent.model_dump(mode="json"),
        "_original_message": original[:_CONTEXT_TEXT_LIMIT]
        if isinstance(original, str)
        else task.message[:_CONTEXT_TEXT_LIMIT],
        "_answers": _bounded_answers(task.resolved_state.get("_answers")),
        **(
            {"_previous_suggestions": task.resolved_state["_previous_suggestions"]}
            if "_previous_suggestions" in task.resolved_state
            else {}
        ),
    }


@dataclass(frozen=True)
class SessionEvent:
    id: int
    event: EventType
    data: dict[str, Any]


@dataclass
class ActiveTask:
    task_id: str
    action: Action | None
    language: Language
    message: str
    target_url: str | None = None
    step_count: int = 1
    status: TaskStatus = "awaiting_action_result"
    model_call_id: str | None = None
    resolved_state: dict[str, Any] = field(default_factory=dict)
    pending_clarification: str | None = None
    intent_kind: str | None = None
    target_name: str | None = None
    auth_handoff: bool = False
    awaiting_newest_order_spotlight: bool = False
    suggestions: dict[str, object] | None = None
    pause_message: str | None = None
    confirmation: ConfirmationLedger | None = None
    mutation_proposal: MutationProposal | None = None
    mutation_kind: Literal["clear_cart", "submit_checkout"] | None = None
    cart_actions: list[Action] = field(default_factory=list)
    cart_operation: str | None = None


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
    last_followup_target: str | None = None
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
        confirmation_registrar: Callable[[str, str, str, str, int], bool] | None = None,
    ) -> None:
        self._planner = planner or ScriptedPlanner()
        self._clock = clock
        self._confirmation_registrar = confirmation_registrar
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

    def _offer_mutation(
        self, task: ActiveTask, snapshot: Snapshot, sequence: int
    ) -> AskShopperAction:
        proposal = next(
            (
                candidate
                for element in snapshot.elements
                if (candidate := classify_guarded_mutation(snapshot, element.id, task.task_id))
                is not None
                and (
                    (
                        task.mutation_kind == "clear_cart"
                        and "/cart/clear" in candidate.target_signature
                    )
                    or (
                        task.mutation_kind == "submit_checkout"
                        and "/checkout/submit" in candidate.target_signature
                    )
                )
            ),
            None,
        )
        if proposal is None:
            raise ValueError("No current Guarded Mutation target is available")
        ledger = ConfirmationLedger(clock=self._clock)
        question_id = ledger.offer(proposal)
        task.confirmation = ledger
        task.mutation_proposal = proposal
        is_arabic = task.language == "ar"
        effect = (
            (
                "إزالة كل المنتجات من السلة الحالية"
                if task.mutation_kind == "clear_cart"
                else "تسجيل طلب خيالي واحد بمحتويات السلة الحالية، دون دفع حقيقي"
            )
            if is_arabic
            else proposal.effect
        )
        question = (
            f"تأكيد الإجراء: {effect}. هل تريد المتابعة؟"
            if is_arabic
            else f"Confirm this action: {effect}. Continue?"
        )
        return AskShopperAction(
            v=1,
            type="ask_shopper",
            task_id=task.task_id,
            action_id=question_id,
            sequence_number=sequence,
            narration=question,
            question=question,
            options=["تأكيد", "إيقاف"] if is_arabic else ["Confirm", "Stop"],
            kind="confirmation",
        )

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

    def begin_interpretation(
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
            self._append(session, "cancelled", {"task_id": session.active_task.task_id})
        previous_target = session.last_followup_target
        followup_target = previous_target if is_deictic_cart_open(text) else None
        session.last_followup_target = None
        resolved_state: dict[str, Any] = {
            "_original_message": text[:_CONTEXT_TEXT_LIMIT],
            "_answers": [],
        }
        if previous_target is not None:
            resolved_state["_previous_target"] = previous_target
        previous_suggestions = (
            session.last_task.suggestions.get("suggestions", [])
            if session.last_task is not None and session.last_task.suggestions
            else []
        )
        if previous_suggestions:
            resolved_state["_previous_suggestions"] = [
                {"id": item["id"], "name": item["name"]}
                for item in previous_suggestions[:3]
                if isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and isinstance(item.get("name"), str)
            ]
        if followup_target is not None:
            resolved_state["target"] = followup_target
        task = ActiveTask(
            task_id=f"task-{uuid4().hex}",
            action=None,
            language=detect_language(text),
            message=text,
            step_count=0,
            status="interpreting",
            model_call_id=f"call-{uuid4().hex}",
            resolved_state=resolved_state,
            pending_clarification="target" if followup_target else None,
        )
        session.active_task = task
        session.last_task = task
        session.last_snapshot = snapshot
        session.conversation.append({"role": "shopper", "text": text})
        self._append(session, "task_started", {"task_id": task.task_id})
        self._append(
            session,
            "narration",
            {
                "task_id": task.task_id,
                "text": "بفهم طلبك الآن…"
                if task.language == "ar"
                else "Understanding your request…",
            },
        )
        self._touch(session)
        return task

    def finish_interpretation(
        self,
        session_id: str,
        task_id: str,
        call_id: str,
        intent: StructuredIntent,
    ) -> ActiveTask | None:
        session = self.get(session_id)
        task = session.active_task
        if task is None or task.task_id != task_id or task.model_call_id != call_id:
            return None
        if task.status != "interpreting" or session.requires_reconciliation:
            return None
        if (
            task.resolved_state
            and "_intent" not in task.resolved_state
            and intent.intent == "find_products"
        ):
            supplied = intent.constraints.model_dump(mode="json", exclude_none=True)
            unresolved = set(intent.missing_fields) | set(intent.conflicting_fields)
            preserved = {
                key: value
                for key, value in task.resolved_state.items()
                if key in type(intent.constraints).model_fields and key not in unresolved
            }
            intent = StructuredIntent.model_validate(
                {
                    **intent.model_dump(mode="json"),
                    "constraints": {**preserved, **supplied},
                }
            )
        if intent.intent in {"off_topic", "unsupported", "help"}:
            summary = (
                "أقدر أساعدك في التسوق داخل المتجر."
                if intent.language == "ar"
                else ("I can help with shopping in this Storefront.")
            )
            self._append(
                session,
                "done",
                {
                    "task_id": task_id,
                    "summary": summary,
                    "language": intent.language,
                },
            )
            task.status = "completed"
            task.model_call_id = None
            session.active_task = None
            session.last_task = task
            session.conversation.append({"role": "copilot", "text": summary})
            self._touch(session)
            return task
        if intent.intent == "open_product" and not intent.needs_clarification:
            allowed = task.resolved_state.get("_previous_suggestions", [])
            if intent.product_id not in {
                item.get("id") for item in allowed if isinstance(item, dict)
            }:
                raise ValueError("Product was not among the verified recommendations")
        if intent.intent == "cart_edit":
            intent = validate_cart_intent(task.message, intent)
            task.cart_operation = intent.cart_operation
            task.cart_actions = plan_cart_edit(
                intent, session.last_snapshot, task_id, task.step_count + 1
            )
            action = task.cart_actions.pop(0)
        elif intent.intent == "mutate":
            validate_mutation_interpretation(task.message, intent)
            task.mutation_kind = intent.mutation_kind
            destination = "/cart" if intent.mutation_kind == "clear_cart" else "/checkout"
            if session.last_snapshot is None:
                raise ValueError("A current Storefront Snapshot is required")
            if urlsplit(session.last_snapshot.url).path == destination:
                action = self._offer_mutation(task, session.last_snapshot, task.step_count + 1)
            else:
                action = NavigateAction(
                    v=1,
                    type="navigate",
                    task_id=task_id,
                    action_id=f"action-{uuid4().hex}",
                    sequence_number=task.step_count + 1,
                    narration=(
                        "هفتح الصفحة عشان أراجع الإجراء قبل تأكيدك."
                        if intent.language == "ar"
                        else "I'll open the page before asking you to confirm."
                    ),
                    url=destination,
                )
        else:
            action = self._planner.plan_intent(
                intent,
                session.last_snapshot,
                ActionIdentity(
                    task_id=task_id,
                    action_id=f"action-{uuid4().hex}",
                    sequence_number=task.step_count + 1,
                ),
            )
        task.action = action
        task.model_call_id = None
        task.language = intent.language
        task.intent_kind = intent.intent
        task.target_name = intent.constraints.target
        task.step_count += 1
        task.target_url = action.url if isinstance(action, NavigateAction) else None
        task.status = (
            "awaiting_answer" if isinstance(action, AskShopperAction) else "awaiting_action_result"
        )
        task.resolved_state = _intent_context(task, intent)
        task.pending_clarification = (
            (intent.missing_fields or intent.conflicting_fields)[0]
            if intent.needs_clarification and (intent.missing_fields or intent.conflicting_fields)
            else None
        )
        self._append(session, "narration", {"task_id": task_id, "text": action.narration})
        self._append(session, "action", {"task_id": task_id, "action": to_wire(action)})
        session.conversation.append({"role": "copilot", "text": action.narration})
        self._touch(session)
        return task

    def finish_catalogue_interpretation(
        self,
        session_id: str,
        task_id: str,
        call_id: str,
        intent: StructuredIntent,
        result: DiscoveryResult,
    ) -> ActiveTask | None:
        session = self.get(session_id)
        task = session.active_task
        if (
            task is None
            or task.task_id != task_id
            or task.model_call_id != call_id
            or task.status != "interpreting"
            or session.requires_reconciliation
        ):
            return None
        if intent.needs_clarification:
            raise ValueError("Incomplete intent cannot publish catalogue suggestions")
        payload = result.to_wire()
        task.suggestions = payload
        task.language = intent.language
        task.intent_kind = intent.intent
        task.model_call_id = None
        task.status = "completed"
        session.active_task = None
        session.last_task = task
        if any(item.label == "styling_suggestion" for item in result.suggestions):
            summary = (
                "دي اقتراحات تنسيق من منتجات المتجر المتاحة."
                if intent.language == "ar"
                else "These are styling suggestions from available Storefront products."
            )
        elif result.exact_count:
            summary = (
                f"وجدت {result.exact_count} منتج مطابق ومتحقق منه."
                if intent.language == "ar"
                else f"Found {result.exact_count} verified exact matches."
            )
        elif result.suggestions:
            if intent.price_preference is not None:
                summary = (
                    "لا يوجد منتج يحقق كل الشروط. رتبت البدائل من الأقل سعراً مع توضيح ما ينقصها."
                    if intent.language == "ar"
                    else (
                        "No product meets every requirement. Alternatives are sorted by price "
                        "with gaps shown."
                    )
                )
            else:
                summary = (
                    "لا توجد منتجات تطابق كل الشروط. هذه بدائل موضّح ما ينقصها."
                    if intent.language == "ar"
                    else "No product meets every requirement. These are labelled alternatives."
                )
        else:
            summary = (
                "لا أقدر أؤكد وجود منتج مناسب من بيانات المتجر الحالية."
                if intent.language == "ar"
                else "I cannot verify a suitable product in the current catalogue."
            )
        self._append(session, "suggestions", {"task_id": task_id, **payload})
        self._append(
            session,
            "done",
            {"task_id": task_id, "summary": summary, "language": intent.language},
        )
        session.conversation.append({"role": "copilot", "text": summary})
        self._touch(session)
        return task

    def begin_answer_interpretation(
        self,
        session_id: str,
        task_id: str,
        question_id: str,
        text: str,
        snapshot: Snapshot,
        tab_id: str | None,
    ) -> ActiveTask:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        task = session.active_task
        if (
            task is None
            or task.task_id != task_id
            or not isinstance(task.action, AskShopperAction)
            or task.action.action_id != question_id
            or task.status != "awaiting_answer"
        ):
            raise ActionResultMismatch("Answer does not match the pending Shopper question")
        if task.step_count >= 8:
            raise TaskConflict("Shopping Task step limit reached")
        task.message = text
        answers = _bounded_answers(task.resolved_state.get("_answers"))
        task.resolved_state["_answers"] = [*answers, text[:_CONTEXT_TEXT_LIMIT]][
            -_CONTEXT_ANSWER_LIMIT:
        ]
        task.action = None
        task.status = "interpreting"
        task.model_call_id = f"call-{uuid4().hex}"
        session.last_snapshot = snapshot
        session.conversation.append({"role": "shopper", "text": text})
        self._append(
            session,
            "narration",
            {
                "task_id": task_id,
                "text": "بفهم إجابتك…" if task.language == "ar" else "Understanding your answer…",
            },
        )
        self._touch(session)
        return task

    def fail_interpretation(
        self,
        session_id: str,
        task_id: str,
        call_id: str,
        reason: InterpretationPauseReason,
        *,
        retry_after_seconds: int | None = None,
    ) -> None:
        session = self.get(session_id)
        task = session.active_task
        if task is None or task.task_id != task_id or task.model_call_id != call_id:
            return
        if task.status != "interpreting":
            return
        task.status = "paused"
        task.model_call_id = None
        messages = {
            "throttled": (
                "وصلنا لحد الطلبات المؤقت لخدمة النموذج. جرّب تاني بعد شوية أو أوقف المهمة.",
                "The model service reached a temporary request limit. "
                "Retry later or stop the task.",
            ),
            "timeout": (
                "انتهت مهلة انتظار خدمة النموذج. جرّب تاني أو أوقف المهمة.",
                "The model service timed out. Retry or stop the task.",
            ),
            "network": (
                "تعذر الاتصال بخدمة النموذج. جرّب تاني أو أوقف المهمة.",
                "The model service could not be reached. Retry or stop the task.",
            ),
            "provider_http": (
                "خدمة النموذج رفضت الطلب أو واجهت خطأ. جرّب تاني أو أوقف المهمة.",
                "The model service rejected the request or failed. Retry or stop the task.",
            ),
            "invalid_response": (
                "استجابة النموذج غير صالحة للتحقق، فتوقفت قبل أي إجراء. جرّب تاني أو أوقف المهمة.",
                "The model response could not be validated, so no action was taken. Retry or stop.",
            ),
            "catalogue_unavailable": (
                "تعذر التحقق من بيانات المنتجات الآن، فتوقفت قبل أي إجراء. "
                "جرّب تاني أو أوقف المهمة.",
                "Product facts could not be verified, so no action was taken. Retry or stop.",
            ),
            "interrupted": (
                "اتقطع طلب الفهم قبل ما يكتمل. جرّب تاني أو أوقف المهمة.",
                "Interpretation was interrupted before completion. Retry or stop the task.",
            ),
            "unexpected": (
                "توقفت المهمة بسبب خطأ غير متوقع؛ السبب الدقيق غير معروف. جرّب تاني أو أوقف المهمة.",
                "An unexpected error paused the task; the exact cause is unknown. Retry or stop.",
            ),
        }
        if reason == "throttled" and retry_after_seconds is not None:
            messages["throttled"] = (
                f"وصلنا لحد استخدام النموذج. انتظر {retry_after_seconds} ثانية قبل إعادة المحاولة. "
                "لم يتم تعديل السلة.",
                f"Model limit reached. Wait {retry_after_seconds} seconds before retrying. "
                "The cart was not changed.",
            )

        message = messages[reason][0 if task.language == "ar" else 1]
        task.pause_message = message
        self._append(session, "error", {"task_id": task_id, "message": message})
        self._touch(session)

    def retry_interpretation(self, session_id: str, task_id: str, tab_id: str | None) -> ActiveTask:
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        task = session.active_task
        if task is None or task.task_id != task_id or task.status != "paused":
            raise TaskConflict("This Shopping Task is not awaiting Retry")
        task.status = "interpreting"
        task.model_call_id = f"call-{uuid4().hex}"
        task.pause_message = None
        self._append(
            session,
            "narration",
            {
                "task_id": task_id,
                "text": "بحاول أفهم طلبك تاني…" if task.language == "ar" else "Trying again…",
            },
        )
        self._touch(session)
        return task

    def submit_message(
        self,
        session_id: str,
        text: str,
        snapshot: Snapshot,
        *,
        replace_active: bool = False,
        tab_id: str | None = None,
    ) -> ActiveTask:
        scripted_mutation = scripted_mutation_intent(text) or scripted_cart_intent(text)
        if scripted_mutation is not None:
            task = self.begin_interpretation(
                session_id,
                text,
                snapshot,
                replace_active=replace_active,
                tab_id=tab_id,
            )
            self.finish_interpretation(
                session_id, task.task_id, task.model_call_id or "", scripted_mutation
            )
            return task
        session = self.get(session_id)
        self.assert_lease(session, tab_id)
        if session.active_task is not None:
            if not replace_active:
                raise TaskConflict("A Shopping Task is already active")
            replaced = session.active_task
            session.active_task = None
            self._append(session, "cancelled", {"task_id": replaced.task_id})
        previous_target = session.last_followup_target
        followup_target = previous_target if is_deictic_cart_open(text) else None
        session.last_followup_target = None
        task_id = f"task-{uuid4().hex}"
        planner_message = "افتح السلة" if followup_target == "cart" else text
        action, scripted_intent = self._planner.plan_with_intent(
            planner_message,
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
            resolved_state={
                "_original_message": text[:_CONTEXT_TEXT_LIMIT],
                "_answers": [],
                **({"_previous_target": previous_target} if previous_target else {}),
                **({"target": followup_target} if followup_target else {}),
            },
            target_url=action.url if isinstance(action, NavigateAction) else None,
            intent_kind=scripted_intent.intent if scripted_intent is not None else None,
            target_name=(
                scripted_intent.constraints.target if scripted_intent is not None else None
            ),
        )
        if scripted_intent is not None:
            task.language = scripted_intent.language
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
        if task.action.options == ["Stop"]:
            if text != "Stop":
                raise ActionResultMismatch("Choose Stop to end this Shopping Task")
            task.status = "cancelled"
            session.last_task = task
            session.active_task = None
            self._append(session, "cancelled", {"task_id": task.task_id})
            self._touch(session)
            return task
        if task.action.kind == "confirmation":
            if (
                task.status != "awaiting_answer"
                or task.confirmation is None
                or task.mutation_proposal is None
            ):
                raise ActionResultMismatch("There is no live Confirmation")
            if text in {"Stop", "إيقاف"}:
                task.confirmation.invalidate()
                task.status = "cancelled"
                session.last_task = task
                session.active_task = None
                self._append(session, "cancelled", {"task_id": task.task_id})
                self._touch(session)
                return task
            expected_answer = "تأكيد" if task.language == "ar" else "Confirm"
            candidate = next(
                (
                    (element, current)
                    for element in snapshot.elements
                    if (current := classify_guarded_mutation(snapshot, element.id, task.task_id))
                    == task.mutation_proposal
                ),
                None,
            )
            if candidate is None or text != expected_answer:
                raise ActionResultMismatch("Confirmation no longer matches the Storefront state")
            element, current = candidate
            if not task.confirmation.can_confirm(question_id, "Confirm", current):
                raise ActionResultMismatch("Confirmation expired or was already used")
            if self._confirmation_registrar is None or not self._confirmation_registrar(
                snapshot.url,
                question_id,
                task.task_id,
                task.mutation_kind or "",
                int(dict(current.arguments)["cart_revision"]),
            ):
                raise ActionResultMismatch("The Storefront could not register this Confirmation")
            if not task.confirmation.confirm(question_id, "Confirm", current):
                raise ActionResultMismatch("Confirmation expired before execution")
            action = GuardedClickAction(
                v=1,
                type="guarded_click",
                task_id=task.task_id,
                action_id=f"action-{uuid4().hex}",
                sequence_number=task.action.sequence_number + 1,
                narration=(
                    "هأنفذ الإجراء اللي أكدته دلوقتي."
                    if task.language == "ar"
                    else "I'll perform the exact action you confirmed now."
                ),
                id=element.id,
                confirmation_id=question_id,
                mutation_kind=task.mutation_kind or "clear_cart",
                target_signature=current.target_signature,
                state_signature=current.state_signature,
                cart_revision=int(dict(current.arguments)["cart_revision"]),
                effect=current.effect,
            )
            task.confirmation = None
            task.action = action
            task.step_count += 1
            task.status = "awaiting_action_result"
            session.last_snapshot = snapshot
            self._append(session, "narration", {"task_id": task.task_id, "text": action.narration})
            self._append(session, "action", {"task_id": task.task_id, "action": to_wire(action)})
            self._touch(session)
            return task
        if task.auth_handoff:
            if text == "Stop":
                task.status = "cancelled"
                session.last_task = task
                session.active_task = None
                self._append(session, "cancelled", {"task_id": task.task_id})
                self._touch(session)
                return task
            if text != "Continue":
                raise ActionResultMismatch("Choose Continue or Stop to resume order history")
            if (
                task.target_url is not None
                and session.last_snapshot is not None
                and is_expected_login_redirect(snapshot, session.last_snapshot, task.target_url)
            ):
                self._touch(session)
                return task
            if task.step_count >= 8:
                raise TaskConflict("Shopping Task step limit reached")
            action = self._planner.plan_orders_resume(
                snapshot,
                ActionIdentity(
                    task_id=task.task_id,
                    action_id=f"action-{uuid4().hex}",
                    sequence_number=task.action.sequence_number + 1,
                ),
                task.language,
                trusted_origin=session.last_snapshot,
            )
            task.action = action
            task.auth_handoff = isinstance(action, AskShopperAction)
            task.awaiting_newest_order_spotlight = isinstance(action, SpotlightAction)
            task.target_url = action.url if isinstance(action, NavigateAction) else None
            task.step_count += 1
            task.status = (
                "awaiting_answer"
                if isinstance(action, AskShopperAction)
                else "awaiting_action_result"
            )
            session.conversation.append({"role": "copilot", "text": action.narration})
            self._touch(session)
            self._append(session, "narration", {"task_id": task.task_id, "text": action.narration})
            self._append(session, "action", {"task_id": task.task_id, "action": to_wire(action)})
            return task
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
        if isinstance(action, NavigateAction):
            task.target_url = action.url
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

    def is_auth_handoff(self, session_id: str, task_id: str, question_id: str) -> bool:
        task = self.get(session_id).active_task
        return bool(
            task is not None
            and task.task_id == task_id
            and task.auth_handoff
            and isinstance(task.action, AskShopperAction)
            and task.action.action_id == question_id
        )

    def is_guarded_confirmation(self, session_id: str, task_id: str, question_id: str) -> bool:
        task = self.get(session_id).active_task
        return bool(
            task is not None
            and task.task_id == task_id
            and task.status == "awaiting_answer"
            and isinstance(task.action, AskShopperAction)
            and task.action.kind == "confirmation"
            and task.action.action_id == question_id
        )

    def is_stop_only_question(self, session_id: str, task_id: str, question_id: str) -> bool:
        task = self.get(session_id).active_task
        return bool(
            task is not None
            and task.task_id == task_id
            and isinstance(task.action, AskShopperAction)
            and task.action.action_id == question_id
            and task.action.options == ["Stop"]
        )

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
        if action is None or task.status != "awaiting_action_result":
            raise ActionResultMismatch("There is no pending Action")
        identity_matches = (
            action_result.task_id == task.task_id
            and action_result.action_id == action.action_id
            and action_result.sequence_number == action.sequence_number
        )
        if not identity_matches:
            raise ActionResultMismatch("Action Result does not match the pending Action")
        if task.cart_operation:
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            same_origin = (
                session.last_snapshot is not None
                and urlsplit(session.last_snapshot.url).netloc
                == urlsplit(action_result.snapshot.url).netloc
                and urlsplit(session.last_snapshot.url).scheme
                == urlsplit(action_result.snapshot.url).scheme
            )
            session.last_snapshot = action_result.snapshot
            success = action_result.status == "ok" and same_origin
            if success and task.cart_actions:
                task.action = task.cart_actions.pop(0)
                task.step_count += 1
                self._append(
                    session, "action", {"task_id": task.task_id, "action": to_wire(task.action)}
                )
            elif success and any(
                e.visible and e.role == "status" and e.name in MESSAGES[task.cart_operation]
                for e in action_result.snapshot.elements
            ):
                summary = MESSAGES[task.cart_operation][0 if task.language == "ar" else 1]
                task.status = "completed"
                session.active_task = None
                session.last_task = task
                session.conversation.append({"role": "copilot", "text": summary})
                self._append(
                    session,
                    "done",
                    {"task_id": task.task_id, "summary": summary, "language": task.language},
                )
            else:
                task.status = "paused"
                task.action = None
                task.cart_actions.clear()
                task.pause_message = (
                    "تعذر تأكيد تعديل السلة؛ لن أكرره تلقائيًا."
                    if task.language == "ar"
                    else "Cart change was not confirmed; I will not repeat it automatically."
                )
                self._append(
                    session, "error", {"task_id": task.task_id, "message": task.pause_message}
                )
            self._touch(session)
            return task
        if isinstance(action, GuardedClickAction):
            destination_url = urlsplit(action_result.snapshot.url)
            origin_url = urlsplit(session.last_snapshot.url) if session.last_snapshot else None
            same_origin = bool(
                origin_url is not None
                and origin_url.scheme in {"http", "https"}
                and (destination_url.scheme, destination_url.netloc)
                == (origin_url.scheme, origin_url.netloc)
            )
            path = destination_url.path
            verified = (
                action_result.status in {"ok", "navigated"}
                and same_origin
                and (
                    (
                        action.mutation_kind == "clear_cart"
                        and path == "/cart"
                        and any(
                            element.visible
                            and element.role == "status"
                            and element.name == "السلة فارغة"
                            for element in action_result.snapshot.elements
                        )
                    )
                    or (
                        action.mutation_kind == "submit_checkout"
                        and path.startswith("/order/complete/")
                        and any(
                            element.visible
                            and element.role == "heading"
                            and element.name == "تم تسجيل طلب خيالي"
                            for element in action_result.snapshot.elements
                        )
                    )
                )
            )
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            session.last_snapshot = action_result.snapshot
            if not verified:
                task.status = "paused"
                task.action = None
                task.pause_message = (
                    "لم أتحقق من نتيجة الإجراء؛ لن أكرره تلقائيًا."
                    if task.language == "ar"
                    else "I couldn't verify the result and won't repeat this action automatically."
                )
                self._append(
                    session,
                    "error",
                    {"task_id": task.task_id, "message": task.pause_message},
                )
            else:
                summary = (
                    "تم إفراغ السلة."
                    if task.mutation_kind == "clear_cart" and task.language == "ar"
                    else "Cart emptied."
                    if task.mutation_kind == "clear_cart"
                    else "تم تسجيل الطلب الخيالي دون دفع حقيقي."
                    if task.language == "ar"
                    else "Fictional order submitted without a real payment."
                )
                task.status = "completed"
                session.active_task = None
                session.last_task = task
                self._append(
                    session,
                    "done",
                    {"task_id": task.task_id, "summary": summary, "language": task.language},
                )
                session.conversation.append({"role": "copilot", "text": summary})
            self._touch(session)
            return task
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
        if (
            task.intent_kind == "navigate"
            and task.target_name == "orders"
            and task.target_url is not None
            and session.last_snapshot is not None
            and is_expected_login_redirect(
                action_result.snapshot, session.last_snapshot, task.target_url
            )
        ):
            handoff = self._planner.plan_orders_resume(
                action_result.snapshot,
                ActionIdentity(
                    task_id=task.task_id,
                    action_id=f"question-{uuid4().hex}",
                    sequence_number=action.sequence_number + 1,
                ),
                task.language,
                trusted_origin=session.last_snapshot,
            )
            if task.step_count >= 8:
                handoff = AskShopperAction(
                    v=1,
                    type="ask_shopper",
                    task_id=task.task_id,
                    action_id=f"question-{uuid4().hex}",
                    sequence_number=action.sequence_number + 1,
                    narration=(
                        "وصلنا لحد الخطوات. أوقف المهمة هنا."
                        if task.language == "ar"
                        else "The step limit is reached. Stop this task here."
                    ),
                    question=(
                        "هل تريد إيقاف المهمة؟"
                        if task.language == "ar"
                        else "Would you like to stop this task?"
                    ),
                    options=["Stop"],
                )
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            task.action = handoff
            task.auth_handoff = True
            task.status = "awaiting_answer"
            task.step_count += 1
            session.last_snapshot = action_result.snapshot
            self._append(session, "narration", {"task_id": task.task_id, "text": handoff.narration})
            self._append(session, "action", {"task_id": task.task_id, "action": to_wire(handoff)})
            session.conversation.append({"role": "copilot", "text": handoff.narration})
            self._touch(session)
            return task
        if task.target_url is not None and not snapshot_matches_url(
            action_result.snapshot, task.target_url, session.last_snapshot
        ):
            identity = ActionIdentity(
                task_id=task.task_id,
                action_id=f"action-{uuid4().hex}",
                sequence_number=action.sequence_number + 1,
            )
            if task.intent_kind in {"navigate", "locate", "open_product"}:
                next_action = AskShopperAction(
                    v=1,
                    type="ask_shopper",
                    task_id=task.task_id,
                    action_id=identity.action_id,
                    sequence_number=identity.sequence_number,
                    narration=(
                        "لم أتمكن من التحقق من الصفحة المطلوبة، لذلك توقفت."
                        if task.language == "ar"
                        else "I couldn't verify the requested page, so I stopped here."
                    ),
                    question=(
                        "هل تريد إيقاف المهمة؟"
                        if task.language == "ar"
                        else "Would you like to stop this task?"
                    ),
                    options=["Stop"],
                )
            else:
                next_action = self._planner.plan_visible_control_fallback(
                    task.target_url,
                    action_result.snapshot,
                    identity,
                    task.language,
                )
            self._append(
                session,
                "narration",
                {"task_id": task.task_id, "text": next_action.narration},
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
            task.status = (
                "awaiting_answer"
                if isinstance(next_action, AskShopperAction)
                else "awaiting_action_result"
            )
            session.last_snapshot = action_result.snapshot
            session.conversation.append({"role": "copilot", "text": next_action.narration})
            self._touch(session)
            return task
        if task.intent_kind == "mutate" and isinstance(action, NavigateAction):
            try:
                next_action = self._offer_mutation(
                    task, action_result.snapshot, action.sequence_number + 1
                )
            except ValueError:
                task.status = "paused"
                task.action = None
                task.pause_message = (
                    "الإجراء المطلوب غير متاح في حالة السلة الحالية."
                    if task.language == "ar"
                    else "That action is unavailable in the current cart state."
                )
                self._append(
                    session, "error", {"task_id": task.task_id, "message": task.pause_message}
                )
            else:
                task.action = next_action
                task.status = "awaiting_answer"
                task.step_count += 1
                self._append(
                    session, "narration", {"task_id": task.task_id, "text": next_action.narration}
                )
                self._append(
                    session, "action", {"task_id": task.task_id, "action": to_wire(next_action)}
                )
                session.conversation.append({"role": "copilot", "text": next_action.narration})
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            session.last_snapshot = action_result.snapshot
            self._touch(session)
            return task
        if (
            task.intent_kind == "navigate"
            and task.target_name == "orders"
            and not task.awaiting_newest_order_spotlight
            and snapshot_matches_url(
                action_result.snapshot, "/account/orders", session.last_snapshot
            )
        ):
            followup = self._planner.plan_orders_resume(
                action_result.snapshot,
                ActionIdentity(
                    task_id=task.task_id,
                    action_id=f"action-{uuid4().hex}",
                    sequence_number=action.sequence_number + 1,
                ),
                task.language,
                trusted_origin=session.last_snapshot,
            )
            session.accepted_results[result_identity] = AcceptedResult(
                task=task, result=action_result
            )
            task.action = followup
            task.auth_handoff = False
            task.awaiting_newest_order_spotlight = isinstance(followup, SpotlightAction)
            task.step_count += 1
            task.status = (
                "awaiting_answer"
                if isinstance(followup, AskShopperAction)
                else "awaiting_action_result"
            )
            session.last_snapshot = action_result.snapshot
            self._append(
                session, "narration", {"task_id": task.task_id, "text": followup.narration}
            )
            self._append(session, "action", {"task_id": task.task_id, "action": to_wire(followup)})
            session.conversation.append({"role": "copilot", "text": followup.narration})
            self._touch(session)
            return task
        if task.intent_kind in {"navigate", "locate", "open_product"}:
            destinations = {
                "cart": ("السلة", "cart"),
                "orders": ("سجل الطلبات", "order history"),
                "checkout": ("الدفع", "checkout"),
                "account": ("الحساب", "account"),
            }
            ar_destination, en_destination = destinations.get(
                task.target_name or "", ("الصفحة", "page")
            )
            if task.intent_kind == "open_product":
                summary = (
                    "تم فتح صفحة المنتج المقترح."
                    if task.language == "ar"
                    else "Opened the recommended product's page."
                )
                narration = summary
            elif task.intent_kind == "navigate" and task.target_name == "orders":
                summary = (
                    "تم فتح سجل الطلبات وتحديد أحدث طلب."
                    if task.language == "ar"
                    else "Opened order history and highlighted the newest order."
                )
                narration = summary
            elif task.intent_kind == "locate":
                if (
                    task.target_name == "orders"
                    and isinstance(action, SpotlightAction)
                    and "account link" in action.narration.lower()
                ):
                    summary = (
                        "أشرت إلى رابط الحساب؛ سجل الطلبات موجود بداخله."
                        if task.language == "ar"
                        else "Pointed to the account link; order history is inside your account."
                    )
                elif (
                    task.target_name == "checkout"
                    and isinstance(action, SpotlightAction)
                    and "cart link" in action.narration.lower()
                ):
                    summary = (
                        "أشرت إلى رابط السلة، ومنها يبدأ الدفع."
                        if task.language == "ar"
                        else "Pointed to the cart link, where checkout starts."
                    )
                else:
                    summary = (
                        f"تم تحديد {ar_destination}."
                        if task.language == "ar"
                        else f"Located the {en_destination}."
                    )
            else:
                summary = (
                    f"تم فتح {ar_destination}."
                    if task.language == "ar"
                    else f"Opened the {en_destination}."
                )
            narration = summary
        else:
            count = _visible_product_count(action_result.snapshot)
            if count is None:
                narration = summary = (
                    "تعذر التحقق من نتائج البحث."
                    if task.language == "ar"
                    else "Couldn't verify the search results."
                )
            elif count == 0:
                narration = summary = (
                    "لا توجد منتجات مطابقة لطلبك."
                    if task.language == "ar"
                    else "No products match your request."
                )
            else:
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
        session.last_followup_target = (
            task.target_name
            if task.intent_kind in {"locate", "navigate"}
            and task.target_name in {"cart", "orders", "checkout", "account"}
            else None
        )
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
        if task.confirmation is not None:
            task.confirmation.invalidate()
        session.last_task = task
        session.active_task = None
        self._append(session, "cancelled", {"task_id": task.task_id})
        self._touch(session)
        return task

    def state(self, session_id: str, tab_id: str) -> dict[str, Any]:
        session = self.get(session_id)
        owned = session.lease_tab_id in {None, tab_id}
        if (
            owned
            and session.active_task is not None
            and session.active_task.confirmation is not None
        ):
            task = session.active_task
            task.confirmation.invalidate()
            task.confirmation = None
            task.mutation_proposal = None
            task.action = None
            task.status = "paused"
            task.pause_message = (
                "انتهى التأكيد بعد تحديث الصفحة. حاول تاني لتأكيد الحالة الحالية."
                if task.language == "ar"
                else "Confirmation expired on refresh. Retry from the current Storefront state."
            )
            self._append(session, "error", {"task_id": task.task_id, "message": task.pause_message})
        if (
            owned
            and session.active_task is not None
            and session.active_task.status == "interpreting"
        ):
            task = session.active_task
            task.status = "paused"
            task.model_call_id = None
            task.pause_message = (
                "اتحدثت الصفحة أثناء فهم الطلب. حاول تاني أو أوقف المهمة."
                if task.language == "ar"
                else "The page refreshed while I was interpreting. Retry or stop this task."
            )
            self._append(
                session,
                "error",
                {
                    "task_id": task.task_id,
                    "message": task.pause_message,
                },
            )
        if (
            owned
            and session.active_task is not None
            and session.active_task.status == "awaiting_action_result"
        ):
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
                    "suggestions": task.suggestions,
                    "pause_message": task.pause_message,
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
            and task.action is not None
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
