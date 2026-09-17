import asyncio
import json
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from agent.planner import ActionIdentity, ScriptedPlanner, UnsupportedShoppingTask
from agent.schemas import ActionResult, Snapshot, to_wire
from agent.sessions import (
    ActionResultMismatch,
    EventType,
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


def encode_sse(event_id: int, event: EventType, data: dict[str, object]) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_app(session_store: SessionStore | None = None) -> FastAPI:
    app = FastAPI(title="Shopping Copilot Agent")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4100"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    planner = ScriptedPlanner()
    sessions = session_store or SessionStore(planner)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent"}

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
            task = sessions.submit_message(
                session_id,
                message.text,
                message.snapshot,
                replace_active=message.replace_active,
                tab_id=x_tab_id,
            )
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except TaskConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except LeaseConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except UnsupportedShoppingTask as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"task_id": task.task_id}

    @app.post("/sessions/{session_id}/tasks/{task_id}/answers", status_code=202)
    async def answer_question(
        session_id: str,
        task_id: str,
        answer: SessionAnswer,
        x_tab_id: str | None = Header(default=None),
    ) -> dict[str, str]:
        try:
            task = sessions.answer(
                session_id,
                task_id,
                answer.question_id,
                answer.text,
                answer.snapshot,
                x_tab_id,
            )
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except (ActionResultMismatch, UnsupportedShoppingTask) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"task_id": task.task_id, "status": "resumed"}

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
