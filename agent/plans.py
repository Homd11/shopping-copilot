"""Multi-part messages: a thin plan beside the Session's one active Shopping Task.

The plan holds only the Shopper's words for each step. It never carries an intent, a product
ID, an element ID or a target: each step is interpreted by the normal path at its own turn,
against the latest observed Snapshot, as its own Shopping Task with its own task id.
Progression is driven by the shared task end (`TaskRuntime.end_task`).
"""

from dataclasses import dataclass, field
from uuid import uuid4

from agent.llm.intent import StructuredIntent
from agent.planner import Language
from agent.session_state import (
    ActivePlan,
    ActiveTask,
    PlanStep,
    Session,
    TaskEnd,
)
from agent.task_runtime import TaskRuntime

# A completed task that ended in the catalogue's exhausted fallback did not do its step.
RETRIEVAL_EXHAUSTED = "retrieval_exhausted"
_GENERIC_FIRST_STEP: dict[str, str] = {"ar": "الطلب الأول", "en": "First request"}


@dataclass(frozen=True)
class PlanSteps:
    """What the first interpretation of a message said about the parts after the first."""

    first_step: str | None = None
    remaining_steps: list[str] = field(default_factory=list)
    skipped_steps: list[str] = field(default_factory=list)
    dialect: str = "unknown"

    @classmethod
    def from_intent(cls, intent: StructuredIntent) -> "PlanSteps":
        return cls(
            intent.first_step,
            list(intent.remaining_steps),
            list(intent.skipped_steps),
            intent.dialect,
        )


def open_plan(
    runtime: TaskRuntime,
    session: Session,
    task: ActiveTask,
    steps: PlanSteps,
    language: Language,
) -> None:
    """Create the plan when the first interpretation yields later steps; otherwise nothing.

    A step's own interpretation never nests a plan, and a plan already running is never
    replaced (an answer to step 1's question is interpreted again and may repeat the steps).
    Called just before the first task's own actions are published.
    """
    if task.plan_position is not None or session.plan is not None or not steps.remaining_steps:
        return
    words = [
        steps.first_step or _GENERIC_FIRST_STEP[language],
        *steps.remaining_steps,
    ]
    plan = ActivePlan(
        plan_id=f"plan-{uuid4().hex}",
        language=language,
        steps=[PlanStep(position=i, text=text) for i, text in enumerate(words, start=1)],
        skipped_steps=list(steps.skipped_steps),
    )
    session.plan = plan
    runtime.append(
        session,
        "plan_created",
        {
            "plan_id": plan.plan_id,
            "language": language,
            "steps": [{"position": s.position, "text": s.text} for s in plan.steps],
        },
    )
    runtime.record(
        session,
        "plan_created",
        plan_id=plan.plan_id,
        step_count=len(plan.steps),
        skipped_count=len(plan.skipped_steps),
        language=language,
        dialect=steps.dialect,
    )
    _mark_running(runtime, session, plan, 0, task)


def _mark_running(
    runtime: TaskRuntime, session: Session, plan: ActivePlan, index: int, task: ActiveTask
) -> None:
    step = plan.steps[index]
    step.status = "running"
    step.task_id = task.task_id
    plan.cursor = index
    task.plan_position = step.position
    runtime.append(
        session,
        "plan_step_started",
        {"plan_id": plan.plan_id, "position": step.position, "task_id": task.task_id},
    )


def _finish_step(
    runtime: TaskRuntime,
    session: Session,
    plan: ActivePlan,
    step: PlanStep,
    outcome: str,
    task: ActiveTask | None,
) -> None:
    step.status = outcome  # type: ignore[assignment]
    runtime.append(
        session,
        "plan_step_finished",
        {"plan_id": plan.plan_id, "position": step.position, "outcome": outcome},
    )
    runtime.record(
        session,
        "plan_step",
        plan_id=plan.plan_id,
        position=step.position,
        outcome=outcome,
        intent_type=task.intent_kind if task is not None else None,
        guarded=bool(task is not None and task.mutation_kind is not None),
    )


def _finish_plan(runtime: TaskRuntime, session: Session, plan: ActivePlan, outcome: str) -> None:
    done = sum(s.status == "done" for s in plan.steps)
    failed = sum(s.status == "failed" for s in plan.steps)
    skipped = sum(s.status == "skipped" for s in plan.steps)
    runtime.append(session, "plan_finished", {"plan_id": plan.plan_id, "outcome": outcome})
    runtime.record(
        session,
        "plan_finished",
        plan_id=plan.plan_id,
        outcome=outcome,
        done_count=done,
        failed_count=failed,
        skipped_count=skipped,
    )
    session.plan = None


def _stop_plan(
    runtime: TaskRuntime, session: Session, plan: ActivePlan, outcome: str, from_index: int
) -> None:
    """Every step from `from_index` on was not reached: skipped, and the plan is over."""
    for step in plan.steps[from_index:]:
        _finish_step(runtime, session, plan, step, "skipped", None)
    _finish_plan(runtime, session, plan, outcome)


def on_task_end(runtime: TaskRuntime, end: TaskEnd) -> None:
    """The one place a plan moves: when the current step's task ends."""
    session, task = end.session, end.task
    plan = session.plan
    if plan is None or task.plan_position is None:
        return
    step = plan.steps[plan.cursor]
    if step.task_id != task.task_id:
        return
    if end.kind != "completed" or end.reason == RETRIEVAL_EXHAUSTED:
        # Paused, cancelled or exhausted: this step failed and nothing later runs.
        # No retry, no report.
        _finish_step(runtime, session, plan, step, "failed", task)
        _stop_plan(
            runtime,
            session,
            plan,
            "cancelled" if end.kind == "cancelled" else "failed",
            plan.cursor + 1,
        )
        return
    _finish_step(runtime, session, plan, step, "done", task)
    following = plan.cursor + 1
    if following >= len(plan.steps):
        _finish_plan(runtime, session, plan, "done")
        return
    _start_step(runtime, session, plan, following)


def _start_step(runtime: TaskRuntime, session: Session, plan: ActivePlan, index: int) -> None:
    from agent.task_interpretation import begin_interpretation

    step = plan.steps[index]
    snapshot = session.last_snapshot
    try:
        if snapshot is None:
            raise ValueError("A current Storefront Snapshot is required")

        def started(task: ActiveTask) -> None:
            # The interpreter must know earlier parts of the Shopper's message are finished.
            task.resolved_state["_plan_step"] = {
                "position": step.position,
                "of": len(plan.steps),
                "earlier_steps_done": True,
            }
            _mark_running(runtime, session, plan, index, task)
            plan.start_pending = task.task_id

        begin_interpretation(
            runtime,
            session.session_id,
            step.text,
            snapshot,
            tab_id=session.lease_tab_id,
            on_started=started,
        )
    except Exception:
        # The next step could not even begin: it failed, and nothing after it runs.
        # Never raised into the request that ended the previous task: that task did end.
        if step.status == "pending":
            _finish_step(runtime, session, plan, step, "failed", None)
            _stop_plan(runtime, session, plan, "failed", index + 1)
