import asyncio
import json
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from agent.planner import ActionIdentity, ScriptedPlanner, UnsupportedShoppingTask
from agent.schemas import ActionResult, Snapshot, to_wire
from agent.sessions import (
    ActionResultMismatch,
    EventType,
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


def encode_sse(event_id: int, event: EventType, data: dict[str, object]) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_app() -> FastAPI:
    app = FastAPI(title="Shopping Copilot Agent")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4100"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    planner = ScriptedPlanner()
    sessions = SessionStore(planner)

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
    async def create_session() -> dict[str, str]:
        session = sessions.create()
        return {"session_id": session.session_id}

    @app.post("/sessions/{session_id}/messages", status_code=202)
    async def submit_message(session_id: str, message: SessionMessage) -> dict[str, str]:
        try:
            task = sessions.submit_message(session_id, message.text, message.snapshot)
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except TaskConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except UnsupportedShoppingTask as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"task_id": task.task_id}

    @app.get("/sessions/{session_id}/events")
    async def stream_events(
        session_id: str,
        request: Request,
        after: int = 0,
        once: bool = False,
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
                    yield encode_sse(event.id, event.event, event.data)
                if once or await request.is_disconnected():
                    return
                await asyncio.sleep(0.1)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post("/sessions/{session_id}/action-results", status_code=202)
    async def accept_action_result(session_id: str, action_result: ActionResult) -> dict[str, str]:
        try:
            task = sessions.accept_result(session_id, action_result)
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except ActionResultMismatch as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"task_id": task.task_id, "status": "accepted"}

    @app.post("/sessions/{session_id}/stop", status_code=202)
    async def stop_task(session_id: str) -> dict[str, str]:
        try:
            task = sessions.stop(session_id)
        except SessionNotFound as error:
            raise HTTPException(status_code=404, detail="Session not found") from error
        except TaskConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"task_id": task.task_id, "status": "cancelled"}

    return app


app = create_app()
