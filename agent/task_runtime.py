"""Shared dependencies and cross-cutting task policy used by task transitions."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from agent.confirmation import (
    ConfirmationLedger,
    classify_guarded_mutation,
)
from agent.planner import (
    ScriptedPlanner,
)
from agent.schemas import (
    Action,
    AskShopperAction,
    Snapshot,
    to_wire,
)
from agent.session_registry import SessionRegistry
from agent.session_state import ActiveTask, EventType, Session, SessionEvent, TaskConflict


@dataclass
class TaskRuntime:
    sessions: SessionRegistry
    planner: ScriptedPlanner
    clock: Callable[[], float]
    confirmation_registrar: Callable[[str, str, str, str, int], bool] | None

    def record_snapshot(self, session: Session, snapshot: Snapshot) -> None:
        location = urlsplit(snapshot.url)
        if session.product_context.origin != (location.scheme, location.netloc):
            session.advice_context.clear()
        session.last_snapshot = snapshot
        session.product_context.observe(
            snapshot, self.planner.storefront, len(session.conversation)
        )

    def require_task_origin(self, task: ActiveTask, snapshot: Snapshot) -> None:
        if task.origin_url is not None:
            original, current = urlsplit(task.origin_url), urlsplit(snapshot.url)
            if (original.scheme, original.netloc) != (current.scheme, current.netloc):
                raise TaskConflict("Continuing a task requires its original Storefront origin")

    def ask_to_stop_uncertain_mutation(
        self, session: Session, task: ActiveTask, action: Action
    ) -> None:
        if task.mutation_kind == "submit_checkout":
            narration = (
                "مش متأكد إذا الطلب الخيالي اتسجل. راجع سجل الطلبات؛ مش هقدمه تاني تلقائيًا."
                if task.language == "ar"
                else "I can't verify whether the fictional order was submitted. "
                "Check order history; I won't submit it again automatically."
            )
        else:
            narration = (
                "مش متأكد إذا تعديل السلة اكتمل. راجع السلة الحالية؛ مش هكرره تلقائيًا."
                if task.language == "ar"
                else "I can't verify whether the cart changed. Review the current cart; "
                "I won't repeat the change automatically."
            )
        question = (
            "أوقف المهمة دي، واطلب التعديل من جديد لو لسه محتاجه."
            if task.language == "ar"
            else "Stop this task, then make a new request only if the change is still needed."
        )
        stop = AskShopperAction(
            v=1,
            type="ask_shopper",
            task_id=task.task_id,
            action_id=f"question-{uuid4().hex}",
            sequence_number=action.sequence_number + 1,
            narration=narration,
            question=question,
            options=["إيقاف"] if task.language == "ar" else ["Stop"],
        )
        task.action = stop
        task.step_count += 1
        task.status = "awaiting_answer"
        task.pause_message = None
        task.cart_actions.clear()
        task.mutation_proposal = None
        self.append(session, "narration", {"task_id": task.task_id, "text": narration})
        self.append(session, "action", {"task_id": task.task_id, "action": to_wire(stop)})
        session.conversation.append({"role": "copilot", "text": narration})

    def offer_mutation(
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
        ledger = ConfirmationLedger(clock=self.clock)
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

    @staticmethod
    def append(session: Session, event: EventType, data: dict[str, Any]) -> None:
        payload = {"session_id": session.session_id, **data}
        session.events.append(SessionEvent(id=len(session.events) + 1, event=event, data=payload))
