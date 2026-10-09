"""HTTP/SSE delivery adapter for session events; no task transition policy."""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import HTTPException, Request
from starlette.responses import StreamingResponse

from agent.session_state import EventType, SessionNotFound
from agent.sessions import SessionStore


def encode_sse(event_id: int, event: EventType, data: dict[str, object]) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def session_event_response(
    sessions: SessionStore,
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

    last_event_id = request.headers.get("last-event-id")
    if last_event_id is not None:
        if not last_event_id.isascii() or not last_event_id.isdecimal():
            raise HTTPException(status_code=400, detail="Invalid event cursor")
        after = max(after, int(last_event_id))

    async def event_stream() -> AsyncIterator[str]:
        cursor = after
        while True:
            if not await request.state.shopper_authorized():
                yield "event: shopper_reset\ndata: {}\n\n"
                return
            try:
                pending = sessions.events_after(session_id, cursor)
            except SessionNotFound:
                yield "event: shopper_reset\ndata: {}\n\n"
                return
            for event in pending:
                if not await request.state.shopper_authorized():
                    yield "event: shopper_reset\ndata: {}\n\n"
                    return
                cursor = event.id
                try:
                    sessions.get(session_id)
                    if event.event == "action" and not sessions.owns_lease(session_id, tab_id):
                        continue
                except SessionNotFound:
                    yield "event: shopper_reset\ndata: {}\n\n"
                    return
                yield encode_sse(event.id, event.event, event.data)
            if once or await request.is_disconnected():
                return
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
