"""ActionResult identity matching and execution progress."""

import re
from urllib.parse import urlsplit
from uuid import uuid4

from agent.cart import MESSAGES, plan_cart_edit
from agent.llm.intent import StructuredIntent
from agent.planner import (
    ActionIdentity,
    is_expected_login_redirect,
    snapshot_matches_url,
)
from agent.schemas import (
    ActionResult,
    AskShopperAction,
    ClickAction,
    GuardedClickAction,
    NavigateAction,
    Snapshot,
    SpotlightAction,
    to_wire,
)
from agent.session_state import (
    AcceptedResult,
    ActionResultMismatch,
    ActiveTask,
)
from agent.task_runtime import TaskRuntime


def _visible_product_count(snapshot: Snapshot) -> int | None:
    counts = {
        int(match.group(1))
        for element in snapshot.elements
        if element.visible and element.role == "heading" and element.level == 2
        if (match := re.fullmatch(r"(\d+) منتجات", element.name.strip())) is not None
    }
    return next(iter(counts)) if len(counts) == 1 else None


def accept_result(
    runtime: TaskRuntime, session_id: str, action_result: ActionResult, tab_id: str | None = None
) -> ActiveTask:
    session = runtime.sessions.get(session_id)
    runtime.sessions.assert_lease(session, tab_id)
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
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        same_origin = (
            session.last_snapshot is not None
            and urlsplit(session.last_snapshot.url).netloc
            == urlsplit(action_result.snapshot.url).netloc
            and urlsplit(session.last_snapshot.url).scheme
            == urlsplit(action_result.snapshot.url).scheme
        )
        runtime.record_snapshot(session, action_result.snapshot)
        if isinstance(action, NavigateAction):
            if (
                same_origin
                and action_result.status in {"ok", "navigated"}
                and urlsplit(action_result.snapshot.url).path == "/cart"
            ):
                intent = StructuredIntent.model_validate(task.resolved_state["_intent"])
                if intent.v >= 8:
                    # Navigation supplied the previously unavailable cart context.
                    # Resolve a DOM target from this fresh snapshot before any edit.
                    task.action = None
                    task.cart_actions.clear()
                    task.cart_operation = None
                    task.status = "interpreting"
                    task.model_call_id = f"call-{uuid4().hex}"
                    runtime.sessions.touch(session)
                    return task
                task.cart_actions = plan_cart_edit(
                    intent, action_result.snapshot, task.task_id, task.step_count + 1
                )
                task.action = task.cart_actions.pop(0)
                task.step_count += 1
                task.status = (
                    "awaiting_answer"
                    if isinstance(task.action, AskShopperAction)
                    else "awaiting_action_result"
                )
                runtime.append(
                    session, "action", {"task_id": task.task_id, "action": to_wire(task.action)}
                )
            else:
                task.status = "paused"
                task.action = None
                task.cart_actions.clear()
                task.pause_message = (
                    "تعذر فتح السلة. حاول تاني."
                    if task.language == "ar"
                    else "Could not open the cart. Retry."
                )
                runtime.append(
                    session, "error", {"task_id": task.task_id, "message": task.pause_message}
                )
            runtime.sessions.touch(session)
            return task
        success = action_result.status == "ok" and same_origin
        if success and task.cart_actions:
            task.action = task.cart_actions.pop(0)
            task.step_count += 1
            runtime.append(
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
            runtime.append(
                session,
                "done",
                {"task_id": task.task_id, "summary": summary, "language": task.language},
            )
        else:
            if isinstance(action, ClickAction):
                runtime.ask_to_stop_uncertain_mutation(session, task, action)
            else:
                task.status = "paused"
                task.action = None
                task.cart_actions.clear()
                task.pause_message = (
                    "تعذر تجهيز تعديل السلة. حاول تاني من الحالة الحالية."
                    if task.language == "ar"
                    else "Could not prepare the cart change. Retry from the current state."
                )
                runtime.append(
                    session, "error", {"task_id": task.task_id, "message": task.pause_message}
                )
        runtime.sessions.touch(session)
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
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        runtime.record_snapshot(session, action_result.snapshot)
        if not verified:
            runtime.ask_to_stop_uncertain_mutation(session, task, action)
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
            runtime.append(
                session,
                "done",
                {"task_id": task.task_id, "summary": summary, "language": task.language},
            )
            session.conversation.append({"role": "copilot", "text": summary})
        runtime.sessions.touch(session)
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
        runtime.append(
            session,
            "narration",
            {"task_id": task.task_id, "text": narration},
        )
        runtime.append(
            session,
            "action",
            {"task_id": task.task_id, "action": to_wire(next_action)},
        )
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        task.action = next_action
        task.step_count += 1
        task.status = "awaiting_answer"
        runtime.record_snapshot(session, action_result.snapshot)
        session.conversation.append({"role": "copilot", "text": narration})
        runtime.sessions.touch(session)
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
        handoff = runtime.planner.plan_orders_resume(
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
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        task.action = handoff
        task.auth_handoff = True
        task.status = "awaiting_answer"
        task.step_count += 1
        runtime.record_snapshot(session, action_result.snapshot)
        runtime.append(session, "narration", {"task_id": task.task_id, "text": handoff.narration})
        runtime.append(session, "action", {"task_id": task.task_id, "action": to_wire(handoff)})
        session.conversation.append({"role": "copilot", "text": handoff.narration})
        runtime.sessions.touch(session)
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
            next_action = runtime.planner.plan_visible_control_fallback(
                task.target_url,
                action_result.snapshot,
                identity,
                task.language,
            )
        runtime.append(
            session,
            "narration",
            {"task_id": task.task_id, "text": next_action.narration},
        )
        runtime.append(
            session,
            "action",
            {"task_id": task.task_id, "action": to_wire(next_action)},
        )
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        task.action = next_action
        task.step_count += 1
        task.status = (
            "awaiting_answer"
            if isinstance(next_action, AskShopperAction)
            else "awaiting_action_result"
        )
        runtime.record_snapshot(session, action_result.snapshot)
        session.conversation.append({"role": "copilot", "text": next_action.narration})
        runtime.sessions.touch(session)
        return task
    if task.intent_kind == "mutate" and isinstance(action, NavigateAction):
        try:
            next_action = runtime.offer_mutation(
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
            runtime.append(
                session, "error", {"task_id": task.task_id, "message": task.pause_message}
            )
        else:
            task.action = next_action
            task.status = "awaiting_answer"
            task.step_count += 1
            runtime.append(
                session, "narration", {"task_id": task.task_id, "text": next_action.narration}
            )
            runtime.append(
                session, "action", {"task_id": task.task_id, "action": to_wire(next_action)}
            )
            session.conversation.append({"role": "copilot", "text": next_action.narration})
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        runtime.record_snapshot(session, action_result.snapshot)
        runtime.sessions.touch(session)
        return task
    if (
        task.intent_kind == "navigate"
        and task.target_name == "orders"
        and not task.awaiting_newest_order_spotlight
        and snapshot_matches_url(action_result.snapshot, "/account/orders", session.last_snapshot)
    ):
        followup = runtime.planner.plan_orders_resume(
            action_result.snapshot,
            ActionIdentity(
                task_id=task.task_id,
                action_id=f"action-{uuid4().hex}",
                sequence_number=action.sequence_number + 1,
            ),
            task.language,
            trusted_origin=session.last_snapshot,
        )
        session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
        task.action = followup
        task.auth_handoff = False
        task.awaiting_newest_order_spotlight = isinstance(followup, SpotlightAction)
        task.step_count += 1
        task.status = (
            "awaiting_answer"
            if isinstance(followup, AskShopperAction)
            else "awaiting_action_result"
        )
        runtime.record_snapshot(session, action_result.snapshot)
        runtime.append(session, "narration", {"task_id": task.task_id, "text": followup.narration})
        runtime.append(session, "action", {"task_id": task.task_id, "action": to_wire(followup)})
        session.conversation.append({"role": "copilot", "text": followup.narration})
        runtime.sessions.touch(session)
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
            summary = (
                "تم عرض المنتجات المطابقة."
                if task.language == "ar"
                else "Matching products are now shown."
            )
    runtime.append(
        session,
        "narration",
        {"task_id": task.task_id, "text": narration},
    )
    runtime.append(
        session,
        "done",
        {"task_id": task.task_id, "summary": summary, "language": task.language},
    )
    session.accepted_results[result_identity] = AcceptedResult(task=task, result=action_result)
    task.status = "completed"
    session.last_task = task
    runtime.record_snapshot(session, action_result.snapshot)
    session.last_followup_target = (
        task.target_name
        if task.intent_kind in {"locate", "navigate"}
        and task.target_name in {"cart", "orders", "checkout", "account"}
        else None
    )
    session.conversation.append({"role": "copilot", "text": summary})
    session.active_task = None
    runtime.sessions.touch(session)
    return task
