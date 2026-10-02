"""Model interpretation lifecycle and bounded conversation context."""

from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from agent.cart import plan_cart_edit, validate_cart_intent
from agent.catalogue import DiscoveryResult
from agent.confirmation import (
    validate_mutation_interpretation,
)
from agent.llm.intent import StructuredIntent
from agent.planner import (
    ActionIdentity,
    detect_language,
)
from agent.product_context import require_known_product
from agent.schemas import (
    AskShopperAction,
    NavigateAction,
    Snapshot,
    to_wire,
)
from agent.session_state import (
    ActionResultMismatch,
    ActiveTask,
    InterpretationPauseReason,
    TaskConflict,
)
from agent.task_runtime import TaskRuntime

_CONTEXT_TEXT_LIMIT = 2000
_CONTEXT_ANSWER_LIMIT = 8


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
        **{
            key: task.resolved_state[key]
            for key in ("_known_products", "_recent_conversation")
            if key in task.resolved_state
        },
    }


def begin_interpretation(
    runtime: TaskRuntime,
    session_id: str,
    text: str,
    snapshot: Snapshot,
    *,
    replace_active: bool = False,
    tab_id: str | None = None,
) -> ActiveTask:
    session = runtime.sessions.get(session_id)
    runtime.sessions.assert_lease(session, tab_id)
    if session.active_task is not None:
        if not replace_active:
            raise TaskConflict("A Shopping Task is already active")
        runtime.append(session, "cancelled", {"task_id": session.active_task.task_id})
    previous_target = session.last_followup_target
    followup_target = None
    session.last_followup_target = None
    resolved_state: dict[str, Any] = {
        "_original_message": text[:_CONTEXT_TEXT_LIMIT],
        "_answers": [],
    }
    location = urlsplit(snapshot.url)
    if session.product_context.origin != (location.scheme, location.netloc):
        session.advice_context.clear()
    if previous_target is not None:
        resolved_state["_previous_target"] = previous_target
    resolved_state.update(
        session.product_context.prepare(snapshot, runtime.planner.storefront, session.conversation)
    )
    if session.advice_context:
        resolved_state["_advice_context"] = session.advice_context.copy()
    if followup_target is not None:
        resolved_state["target"] = followup_target
    task = ActiveTask(
        task_id=f"task-{uuid4().hex}",
        action=None,
        language=detect_language(text),
        message=text,
        step_count=0,
        status="interpreting",
        origin_url=snapshot.url,
        model_call_id=f"call-{uuid4().hex}",
        resolved_state=resolved_state,
        pending_clarification="target" if followup_target else None,
    )
    session.active_task = task
    session.last_task = task
    runtime.record_snapshot(session, snapshot)
    session.conversation.append({"role": "shopper", "text": text})
    runtime.append(session, "task_started", {"task_id": task.task_id})
    runtime.append(
        session,
        "narration",
        {
            "task_id": task.task_id,
            "text": "بفهم طلبك الآن…" if task.language == "ar" else "Understanding your request…",
        },
    )
    runtime.sessions.touch(session)
    return task


def finish_interpretation(
    runtime: TaskRuntime,
    session_id: str,
    task_id: str,
    call_id: str,
    intent: StructuredIntent,
) -> ActiveTask | None:
    session = runtime.sessions.get(session_id)
    task = session.active_task
    if task is None or task.task_id != task_id or task.model_call_id != call_id:
        return None
    if task.status != "interpreting" or session.requires_reconciliation:
        return None
    if session.last_snapshot is not None:
        runtime.require_task_origin(task, session.last_snapshot)
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
        runtime.append(
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
        runtime.sessions.touch(session)
        return task
    if intent.intent == "open_product" and not intent.needs_clarification:
        require_known_product(
            intent.product_id,
            task.resolved_state,
            session.last_snapshot,
            runtime.planner.storefront,
        )
    if intent.intent == "cart_edit":
        intent = validate_cart_intent(task.message, intent, session.last_snapshot)
    if intent.intent == "cart_edit" and not intent.needs_clarification:
        task.cart_operation = intent.cart_operation
        if (
            intent.cart_operation in {"quantity", "remove"}
            and session.last_snapshot is not None
            and urlsplit(session.last_snapshot.url).path != "/cart"
        ):
            task.cart_actions = [
                NavigateAction(
                    v=1,
                    type="navigate",
                    task_id=task_id,
                    action_id=f"action-{uuid4().hex}",
                    sequence_number=task.step_count + 1,
                    narration="هفتح السلة عشان أعدّل المنتج المطلوب."
                    if intent.language == "ar"
                    else "I'll open the cart to find the requested item.",
                    url="/cart",
                )
            ]
        else:
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
            action = runtime.offer_mutation(task, session.last_snapshot, task.step_count + 1)
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
        action = runtime.planner.plan_intent(
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
    if task.cart_operation and isinstance(action, AskShopperAction) and not action.options:
        # The next model call needs the runtime question as well as the draft intent.
        task.pending_clarification = action.question
    if (
        intent.intent == "open_product"
        and task.pending_clarification == "product_id"
        and isinstance(action, AskShopperAction)
    ):
        action.options = [
            item["name"]
            for item in task.resolved_state.get("_previous_suggestions", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ][:3]
    runtime.append(session, "narration", {"task_id": task_id, "text": action.narration})
    runtime.append(session, "action", {"task_id": task_id, "action": to_wire(action)})
    session.conversation.append({"role": "copilot", "text": action.narration})
    runtime.sessions.touch(session)
    return task


def finish_catalogue_interpretation(
    runtime: TaskRuntime,
    session_id: str,
    task_id: str,
    call_id: str,
    intent: StructuredIntent,
    result: DiscoveryResult,
    *,
    advice_text: str | None = None,
) -> ActiveTask | None:
    session = runtime.sessions.get(session_id)
    task = session.active_task
    if (
        task is None
        or task.task_id != task_id
        or task.model_call_id != call_id
        or task.status != "interpreting"
        or session.requires_reconciliation
    ):
        return None
    if intent.needs_clarification and intent.intent != "advice":
        raise ValueError("Incomplete intent cannot publish catalogue suggestions")
    if session.last_snapshot is not None:
        runtime.require_task_origin(task, session.last_snapshot)
    payload = result.to_wire()
    session.product_context.remember_suggestions(payload["suggestions"])
    task.suggestions = payload
    task.resolved_state = _intent_context(task, intent)
    if advice_text is not None:
        session.advice_context = intent.model_dump(
            mode="json",
            include={
                "constraints",
                "catalogue_requirements",
                "price_preference",
                "owned_item",
                "owned_items",
                "desired_wear_position",
                "preferred_colors",
                "subjective_preferences",
                "request_mode",
            },
        )
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
    if advice_text is not None:
        summary = advice_text
    runtime.append(session, "suggestions", {"task_id": task_id, **payload})
    runtime.append(
        session,
        "done",
        {"task_id": task_id, "summary": summary, "language": intent.language},
    )
    session.conversation.append({"role": "copilot", "text": summary})
    runtime.sessions.touch(session)
    return task


def begin_answer_interpretation(
    runtime: TaskRuntime,
    session_id: str,
    task_id: str,
    question_id: str,
    text: str,
    snapshot: Snapshot,
    tab_id: str | None,
) -> ActiveTask:
    session = runtime.sessions.get(session_id)
    runtime.sessions.assert_lease(session, tab_id)
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
    runtime.require_task_origin(task, snapshot)
    selected = None
    if task.intent_kind == "open_product" and task.pending_clarification == "product_id":
        candidates = [
            item
            for item in task.resolved_state.get("_previous_suggestions", [])
            if isinstance(item, dict) and item.get("name") == text
        ]
        if len(candidates) == 1 and text in task.action.options:
            selected = candidates[0]
    task.message = text
    answers = _bounded_answers(task.resolved_state.get("_answers"))
    task.resolved_state["_answers"] = [*answers, text[:_CONTEXT_TEXT_LIMIT]][
        -_CONTEXT_ANSWER_LIMIT:
    ]
    task.action = None
    task.status = "interpreting"
    task.model_call_id = f"call-{uuid4().hex}"
    runtime.record_snapshot(session, snapshot)
    session.conversation.append({"role": "shopper", "text": text})
    runtime.append(
        session,
        "narration",
        {
            "task_id": task_id,
            "text": "بفهم إجابتك…" if task.language == "ar" else "Understanding your answer…",
        },
    )
    runtime.sessions.touch(session)
    if selected is not None:
        # The answer is bound to this question's verified choices. No model
        # is needed to reinterpret an exact product button selection.
        intent = StructuredIntent.model_validate(
            {
                "v": 7,
                "language": task.language,
                "dialect": "unknown",
                "intent": "open_product",
                "constraints": {},
                "product_id": selected["id"],
                "navigation_source": text,
                "missing_fields": [],
                "needs_clarification": False,
            }
        )
        finish_interpretation(runtime, session_id, task_id, task.model_call_id, intent)
    return task


def fail_interpretation(
    runtime: TaskRuntime,
    session_id: str,
    task_id: str,
    call_id: str,
    reason: InterpretationPauseReason,
    *,
    retry_after_seconds: int | None = None,
) -> None:
    session = runtime.sessions.get(session_id)
    task = session.active_task
    if task is None or task.task_id != task_id or task.model_call_id != call_id:
        return
    if task.status != "interpreting":
        return
    task.status = "paused"
    task.model_call_id = None
    messages = {
        "budget": (
            "توقفنا قبل إرسال الطلب للحفاظ على ميزانية التجربة. راجع حد الإنفاق المتاح.",
            "Stopped before sending the request to protect the trial budget. "
            "Check the available spending allowance.",
        ),
        "throttled": (
            "وصلنا لحد الطلبات المؤقت لخدمة النموذج. جرّب تاني بعد شوية أو أوقف المهمة.",
            "The model service reached a temporary request limit. Retry later or stop the task.",
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
            "تعذر التحقق من بيانات المنتجات الآن، فتوقفت قبل أي إجراء. جرّب تاني أو أوقف المهمة.",
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
    runtime.append(session, "error", {"task_id": task_id, "message": message})
    runtime.sessions.touch(session)


def retry_interpretation(
    runtime: TaskRuntime, session_id: str, task_id: str, tab_id: str | None, snapshot: Snapshot
) -> ActiveTask:
    session = runtime.sessions.get(session_id)
    runtime.sessions.assert_lease(session, tab_id)
    task = session.active_task
    if task is None or task.task_id != task_id or task.status != "paused":
        raise TaskConflict("This Shopping Task is not awaiting Retry")
    runtime.require_task_origin(task, snapshot)
    previous = urlsplit(session.last_snapshot.url) if session.last_snapshot else None
    current = urlsplit(snapshot.url)
    if previous is None or (previous.scheme, previous.netloc) != (
        current.scheme,
        current.netloc,
    ):
        raise TaskConflict("Retry requires the current Storefront origin")
    runtime.record_snapshot(session, snapshot)
    task.status = "interpreting"
    task.model_call_id = f"call-{uuid4().hex}"
    task.pause_message = None
    runtime.append(
        session,
        "narration",
        {
            "task_id": task_id,
            "text": "بحاول أفهم طلبك تاني…" if task.language == "ar" else "Trying again…",
        },
    )
    runtime.sessions.touch(session)
    return task
