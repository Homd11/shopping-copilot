import asyncio
import json
import os
from collections.abc import AsyncIterator, Callable
from time import monotonic
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from agent.catalogue import CatalogueReader, HttpCatalogueReader, evaluate_catalogue
from agent.llm import LLMClient, LLMSettings, build_llm_client, interpret_message, load_llm_settings
from agent.llm.groq import GroqRateLimitError
from agent.planner import ActionIdentity, ScriptedPlanner, UnsupportedShoppingTask
from agent.schemas import ActionResult, Snapshot, to_wire
from agent.sessions import (
    ActionResultMismatch,
    EventType,
    InterpretationPauseReason,
    LeaseConflict,
    SessionExpired,
    SessionNotFound,
    SessionStore,
    TaskConflict,
)


class StepRequest(BaseModel):
    message: str
    snapshot: Snapshot


class SessionMessage(BaseModel):
    text: str
    snapshot: Snapshot
    replace_active: bool = False


class SessionAnswer(BaseModel):
    question_id: str
    text: str
    snapshot: Snapshot


class SessionCreate(BaseModel):
    tab_id: str | None = None


class ReconcileRequest(BaseModel):
    snapshot: Snapshot


class TakeoverRequest(BaseModel):
    tab_id: str


class AdvanceTestTime(BaseModel):
    seconds: float


def encode_sse(event_id: int, event: EventType, data: dict[str, object]) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def interpretation_pause_reason(error: Exception) -> InterpretationPauseReason:
    if isinstance(error, GroqRateLimitError):
        return "throttled"
    if isinstance(error, httpx.HTTPStatusError):
        return "throttled" if error.response.status_code == 429 else "provider_http"
    if isinstance(error, httpx.TimeoutException):
        return "timeout"
    if isinstance(error, httpx.TransportError):
        return "network"
    if isinstance(error, ValueError):
        return "invalid_response"
    return "unexpected"


def register_storefront_confirmation(
    snapshot_url: str,
    token: str,
    task_id: str,
    kind: str,
    cart_revision: int,
) -> bool:
    parsed = urlsplit(snapshot_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1"}
        or parsed.port != 4000
    ):
        return False
    try:
        response = httpx.post(
            f"{parsed.scheme}://{parsed.netloc}/__copilot/confirmations",
            json={
                "token": token,
                "task_id": task_id,
                "kind": kind,
                "cart_revision": cart_revision,
            },
            timeout=2.0,
        )
    except httpx.HTTPError:
        return False
    return response.status_code == 201


def create_app(
    session_store: SessionStore | None = None,
    llm_settings: LLMSettings | None = None,
    llm_client: LLMClient | None = None,
    catalogue_reader: CatalogueReader | None = None,
    confirmation_registrar: Callable[[str, str, str, str, int], bool] | None = None,
) -> FastAPI:
    settings = llm_settings or load_llm_settings()
    llm_client = llm_client or build_llm_client(settings)
    app = FastAPI(title="Shopping Copilot Agent")
    app.state.llm_settings = settings
    app.state.llm_client = llm_client
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4100"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    planner = ScriptedPlanner()
    test_clock_enabled = (
        settings.provider == "scripted" and os.environ.get("EVAL_TEST_CLOCK") == "1"
    )
    clock_offset = [0.0]

    def session_clock() -> float:
        return monotonic() + clock_offset[0]

    sessions = session_store or SessionStore(
        planner,
        clock=session_clock,
        confirmation_registrar=confirmation_registrar or register_storefront_confirmation,
    )
    catalogue_reader = catalogue_reader or HttpCatalogueReader()

    async def run_interpretation(session_id: str, task_id: str, call_id: str) -> None:
        task = sessions.get(session_id).active_task
        if task is None or task.task_id != task_id or task.model_call_id != call_id:
            return
        phase = "intent"
        try:
            intent = await interpret_message(
                llm_client,
                task.message,
                storefront=planner.storefront,
                resolved_state=task.resolved_state,
                pending_clarification=task.pending_clarification,
            )
            if (
                intent.intent == "find_products"
                and not intent.needs_clarification
                and (
                    intent.catalogue_requirements
                    or intent.price_preference is not None
                    or intent.desired_wear_position is not None
                    or intent.request_mode in {"recommend", "style"}
                    or intent.context_items
                )
            ):
                phase = "catalogue"
                catalogue = await catalogue_reader.read()
                result = evaluate_catalogue(catalogue, intent)
                sessions.finish_catalogue_interpretation(
                    session_id, task_id, call_id, intent, result
                )
                return
            sessions.finish_interpretation(session_id, task_id, call_id, intent)
        except asyncio.CancelledError:
            sessions.fail_interpretation(session_id, task_id, call_id, "interrupted")
            raise
        except Exception as error:
            reason = (
                "catalogue_unavailable"
                if phase == "catalogue"
                else interpretation_pause_reason(error)
            )
            sessions.fail_interpretation(
                session_id,
                task_id,
                call_id,
                reason,
                retry_after_seconds=getattr(error, "retry_after_seconds", None),
            )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent"}

    if test_clock_enabled:

        @app.post("/__test/advance-time", status_code=204)
        async def advance_test_time(request: AdvanceTestTime) -> None:
            if not 0 < request.seconds <= 120:
                raise HTTPException(status_code=400, detail="Invalid test clock advance")
            clock_offset[0] += request.seconds

    @app.post("/step")
    async def step(request: StepRequest) -> dict[str, object]:
        try:
            action = planner.plan(
                request.message,
                request.snapshot,
                ActionIdentity(
                    task_id=f"task-{uuid4().hex}",
                    action_id=f"action-{uuid4().hex}",
                    sequence_number=1,
                ),
            )
        except UnsupportedShoppingTask as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return to_wire(action)

    @app.post("/sessions", status_code=201)
    async def create_session(request: SessionCreate | None = None) -> dict[str, str]:
        session = sessions.create(request.tab_id if request is not None else None)
        return {"session_id": session.session_id}

    @app.post("/sessions/{session_id}/messages", status_code=202)
    async def submit_message(
        session_id: str,
        message: SessionMessage,
        x_tab_id: str | None = Header(default=None),
    ) -> dict[str, str]:
        try:
            if settings.provider == "scripted":
                task = sessions.submit_message(
                    session_id,
                    message.text,
                    message.snapshot,
                    replace_active=message.replace_active,
                    tab_id=x_tab_id,
                )
            else:
                task = sessions.begin_interpretation(
                    session_id,
                    message.text,
                    message.snapshot,
                    replace_active=message.replace_active,
                    tab_id=x_tab_id,
                )
                await run_interpretation(session_id, task.task_id, task.model_call_id or "")
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except TaskConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except LeaseConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except UnsupportedShoppingTask as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"task_id": task.task_id}

    @app.post("/sessions/{session_id}/tasks/{task_id}/retry", status_code=202)
    async def retry_task(
        session_id: str, task_id: str, x_tab_id: str | None = Header(default=None)
    ) -> dict[str, str]:
        try:
            task = sessions.retry_interpretation(session_id, task_id, x_tab_id)
            await run_interpretation(session_id, task_id, task.model_call_id or "")
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except (TaskConflict, LeaseConflict) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"task_id": task_id, "status": "retried"}

    @app.post("/sessions/{session_id}/tasks/{task_id}/answers", status_code=202)
    async def answer_question(
        session_id: str,
        task_id: str,
        answer: SessionAnswer,
        x_tab_id: str | None = Header(default=None),
    ) -> dict[str, str]:
        try:
            if (
                settings.provider == "scripted"
                or sessions.is_auth_handoff(session_id, task_id, answer.question_id)
                or sessions.is_guarded_confirmation(session_id, task_id, answer.question_id)
                or sessions.is_stop_only_question(session_id, task_id, answer.question_id)
            ):
                task = sessions.answer(
                    session_id,
                    task_id,
                    answer.question_id,
                    answer.text,
                    answer.snapshot,
                    x_tab_id,
                )
            else:
                task = sessions.begin_answer_interpretation(
                    session_id,
                    task_id,
                    answer.question_id,
                    answer.text,
                    answer.snapshot,
                    x_tab_id,
                )
                await run_interpretation(session_id, task_id, task.model_call_id or "")
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except (
            ActionResultMismatch,
            UnsupportedShoppingTask,
            TaskConflict,
            LeaseConflict,
        ) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {
            "task_id": task.task_id,
            "status": (
                "awaiting_login"
                if task.auth_handoff
                and task.action is not None
                and task.action.action_id == answer.question_id
                else "resumed"
            ),
        }

    @app.get("/sessions/{session_id}/events")
    async def stream_events(
        session_id: str,
        request: Request,
        after: int = 0,
        once: bool = False,
        tab_id: str | None = None,
    ) -> StreamingResponse:
        try:
            sessions.get(session_id)
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error

        async def event_stream() -> AsyncIterator[str]:
            cursor = after
            while True:
                pending = sessions.events_after(session_id, cursor)
                for event in pending:
                    cursor = event.id
                    if event.event == "action" and not sessions.owns_lease(session_id, tab_id):
                        continue
                    yield encode_sse(event.id, event.event, event.data)
                if once or await request.is_disconnected():
                    return
                await asyncio.sleep(0.1)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post("/sessions/{session_id}/action-results", status_code=202)
    async def accept_action_result(
        session_id: str,
        action_result: ActionResult,
        x_tab_id: str | None = Header(default=None),
    ) -> dict[str, str]:
        try:
            task = sessions.accept_result(session_id, action_result, x_tab_id)
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except (ActionResultMismatch, LeaseConflict) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"task_id": task.task_id, "status": "accepted"}

    @app.post("/sessions/{session_id}/stop", status_code=202)
    async def stop_task(
        session_id: str, x_tab_id: str | None = Header(default=None)
    ) -> dict[str, str]:
        try:
            task = sessions.stop(session_id, x_tab_id)
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except (TaskConflict, LeaseConflict) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"task_id": task.task_id, "status": "cancelled"}

    @app.get("/sessions/{session_id}/state")
    async def session_state(session_id: str, tab_id: str) -> dict[str, object]:
        try:
            return sessions.state(session_id, tab_id)
        except SessionExpired as error:
            raise HTTPException(status_code=410, detail="Session expired") from error
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error

    @app.post("/sessions/{session_id}/reconcile")
    async def reconcile_session(
        session_id: str,
        request: ReconcileRequest,
        x_tab_id: str = Header(),
    ) -> dict[str, object]:
        try:
            return sessions.reconcile(session_id, x_tab_id, request.snapshot)
        except SessionExpired as error:
            raise HTTPException(status_code=410, detail="Session expired") from error
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except LeaseConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/sessions/{session_id}/takeover")
    async def takeover_session(session_id: str, request: TakeoverRequest) -> dict[str, object]:
        try:
            sessions.takeover(session_id, request.tab_id)
            return sessions.state(session_id, request.tab_id)
        except SessionExpired as error:
            raise HTTPException(status_code=410, detail="Session expired") from error
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error

    return app


app = create_app()
