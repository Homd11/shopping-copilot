import asyncio
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from time import monotonic
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from agent.advice import build_advice_request, compose_advice, prepare_advice
from agent.catalogue import CatalogueReader, HttpCatalogueReader, evaluate_catalogue
from agent.catalogue_client import CatalogueReadError
from agent.catalogue_turn import CatalogueTurnInterrupted, configured_client, prepare_turn
from agent.llm import LLMClient, LLMSettings, build_llm_client, interpret_message, load_llm_settings
from agent.llm.gemini import GeminiRateLimitError
from agent.llm.groq import GroqRateLimitError
from agent.llm.openrouter import OpenRouterBudgetError
from agent.planner import ActionIdentity, ScriptedPlanner, UnsupportedShoppingTask
from agent.schemas import ActionResult, Snapshot, to_wire
from agent.session_stream import encode_sse as encode_sse
from agent.session_stream import session_event_response
from agent.sessions import (
    ActionResultMismatch,
    InterpretationPauseReason,
    LeaseConflict,
    SessionExpired,
    SessionNotFound,
    SessionStore,
    TaskConflict,
)
from agent.shopper_access import ShopperBinding
from agent.shopper_http import install_shopper_http
from agent.speech import MAX_AUDIO_BYTES, OpenRouterSpeechTranscriber, SpeechTranscriber
from agent.storefront_service import StorefrontService, identity_config


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


class RetryRequest(BaseModel):
    snapshot: Snapshot


class TakeoverRequest(BaseModel):
    tab_id: str


class AdvanceTestTime(BaseModel):
    seconds: float


def interpretation_pause_reason(error: Exception) -> InterpretationPauseReason:
    if isinstance(error, OpenRouterBudgetError):
        return "budget"
    if isinstance(error, GroqRateLimitError | GeminiRateLimitError):
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


def create_app(
    session_store: SessionStore | None = None,
    llm_settings: LLMSettings | None = None,
    llm_client: LLMClient | None = None,
    catalogue_reader: CatalogueReader | None = None,
    catalogue_client=None,
    catalogue_retrieval_enabled: bool | None = None,
    confirmation_registrar: Callable[[ShopperBinding | None, str, str, str, str, int], bool]
    | None = None,
    speech_transcriber: SpeechTranscriber | None = None,
    storefront_service: StorefrontService | None = None,
    evaluation: bool = False,
) -> FastAPI:
    settings = llm_settings or load_llm_settings()
    llm_client = llm_client or build_llm_client(settings)
    identity_settings = identity_config()
    service = storefront_service or StorefrontService(identity_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.storefront_service.validate_configuration()
        try:
            yield
        finally:
            close = getattr(app.state.storefront_service, "aclose", None)
            if close is not None:
                await close()

    app = FastAPI(title="Shopping Copilot Agent", lifespan=lifespan)
    app.state.llm_settings = settings
    app.state.llm_client = llm_client
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
        confirmation_registrar=confirmation_registrar or service.register_confirmation,
    )
    install_shopper_http(
        app,
        sessions,
        service,
        panel_origin=identity_settings["panel_origin"],
        evaluation=settings.provider == "scripted"
        and (evaluation or os.environ.get("COPILOT_EVALUATION") == "1"),
    )
    catalogue_reader = catalogue_reader or HttpCatalogueReader()

    retrieval_enabled = (
        os.environ.get("CATALOGUE_RETRIEVAL_ENABLED") == "1"
        if catalogue_retrieval_enabled is None
        else catalogue_retrieval_enabled
    )

    active_interpretations: set[tuple[str, str, str]] = set()

    async def verify_owner(session_id: str) -> None:
        owner = sessions.get(session_id).shopper
        if (
            owner is None
            or not await app.state.storefront_service.validate(owner)
            or not app.state.shopper_access.owns_session(session_id, owner)
        ):
            raise SessionNotFound(session_id)

    async def run_interpretation(session_id: str, task_id: str, call_id: str) -> None:
        task = sessions.get(session_id).active_task
        if task is None or task.task_id != task_id or task.model_call_id != call_id:
            return
        identity = (session_id, task_id, call_id)
        if identity in active_interpretations:
            return
        active_interpretations.add(identity)
        observed = sessions.get(session_id).last_snapshot
        observed = observed.model_copy(deep=True) if observed is not None else None
        phase = "intent"
        try:
            await verify_owner(session_id)
            if retrieval_enabled:
                phase = "catalogue"

                async def ensure_active():
                    current = sessions.get(session_id)
                    if (
                        current.active_task is not task
                        or task.model_call_id != call_id
                        or task.status != "interpreting"
                        or current.requires_reconciliation
                        or current.last_snapshot != observed
                    ):
                        raise CatalogueTurnInterrupted()
                    await verify_owner(session_id)
                    # Ownership validation awaits external I/O; recheck task identity afterwards.
                    current = sessions.get(session_id)
                    if (
                        current.active_task is not task
                        or task.model_call_id != call_id
                        or task.status != "interpreting"
                        or current.requires_reconciliation
                        or current.last_snapshot != observed
                    ):
                        raise CatalogueTurnInterrupted()

                await ensure_active()
                reader = catalogue_client or await configured_client(identity_settings)
                await ensure_active()
                phase = "intent"
                prepared = await prepare_turn(
                    task, observed, planner.storefront, llm_client, reader, ensure_active
                )
                await ensure_active()
                sessions.get(session_id).product_context.remember_catalogue(prepared.references)
                # Remember verified identities only, never DOM targets or mutation authority.
                task.resolved_state["_known_products"] = [
                    *task.resolved_state.get("_known_products", []),
                    *prepared.references,
                ][-24:]
                if prepared.evidence is not None:
                    sessions.finish_catalogue_interpretation(
                        session_id,
                        task_id,
                        call_id,
                        prepared.intent,
                        prepared.evidence.discovery,
                        advice_text=prepared.summary,
                    )
                    session = sessions.get(session_id)
                    session.advice_context["retrieval_requirements"] = list(
                        prepared.evidence.requirements
                    )
                    session.advice_context["unverified_requirements"] = list(
                        prepared.evidence.unverified_requirements
                    )
                else:
                    sessions.finish_interpretation(session_id, task_id, call_id, prepared.intent)
                return
            intent = await interpret_message(
                llm_client,
                task.message,
                storefront=planner.storefront,
                resolved_state=task.resolved_state,
                pending_clarification=task.pending_clarification,
                snapshot=observed,
            )
            await verify_owner(session_id)
            if sessions.get(session_id).last_snapshot != observed:
                sessions.fail_interpretation(session_id, task_id, call_id, "interrupted")
                return
            catalogue_discovery = (
                intent.intent == "find_products"
                and not intent.needs_clarification
                and (
                    intent.catalogue_requirements
                    or intent.price_preference is not None
                    or intent.desired_wear_position is not None
                    or intent.request_mode in {"recommend", "style"}
                    or intent.context_items
                )
            )
            if intent.v >= 9 and (intent.intent == "advice" or catalogue_discovery):
                phase = "catalogue"
                catalogue = await catalogue_reader.read()
                evidence = prepare_advice(catalogue, intent)
                current = sessions.get(session_id)
                if current.active_task is not task or task.model_call_id != call_id:
                    return
                if (
                    intent.intent != "advice"
                    and intent.request_mode == "browse"
                    and not evidence.discovery.exact_count
                ):
                    await verify_owner(session_id)
                    sessions.finish_catalogue_interpretation(
                        session_id, task_id, call_id, intent, evidence.discovery
                    )
                    return
                phase = "advice"
                await verify_owner(session_id)
                try:
                    summary = await compose_advice(
                        llm_client,
                        build_advice_request(
                            task.message, intent, evidence, task.resolved_state, observed
                        ),
                        evidence,
                    )
                except (
                    ValueError,
                    httpx.HTTPError,
                    OpenRouterBudgetError,
                    GroqRateLimitError,
                    GeminiRateLimitError,
                ):
                    summary = (
                        "مش قادر أقدّم نصيحة موثوقة دلوقتي. "
                        "أي منتجات ظاهرة مبنية على بيانات المتجر؛ "
                        "ما غيّرتش حاجة في السلة."
                        if intent.language == "ar"
                        else "I couldn't prepare reliable advice right now. Any products shown use "
                        "verified catalogue data; your cart has not changed."
                    )
                await verify_owner(session_id)
                if sessions.get(session_id).last_snapshot != observed:
                    sessions.fail_interpretation(session_id, task_id, call_id, "interrupted")
                    return
                await verify_owner(session_id)
                sessions.finish_catalogue_interpretation(
                    session_id, task_id, call_id, intent, evidence.discovery, advice_text=summary
                )
                return
            if catalogue_discovery:
                phase = "catalogue"
                catalogue = await catalogue_reader.read()
                result = evaluate_catalogue(catalogue, intent)
                await verify_owner(session_id)
                sessions.finish_catalogue_interpretation(
                    session_id, task_id, call_id, intent, result
                )
                return
            await verify_owner(session_id)
            sessions.finish_interpretation(session_id, task_id, call_id, intent)
        except CatalogueTurnInterrupted:
            sessions.fail_interpretation(session_id, task_id, call_id, "interrupted")
            return
        except SessionNotFound:
            return
        except asyncio.CancelledError:
            sessions.fail_interpretation(session_id, task_id, call_id, "interrupted")
            raise
        except Exception as error:
            reason = (
                "catalogue_unavailable"
                if phase == "catalogue" or isinstance(error, CatalogueReadError)
                else interpretation_pause_reason(error)
            )
            sessions.fail_interpretation(
                session_id,
                task_id,
                call_id,
                reason,
                retry_after_seconds=getattr(error, "retry_after_seconds", None),
            )
        finally:
            active_interpretations.discard(identity)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent"}

    @app.get("/speech/availability")
    async def speech_availability() -> dict[str, bool]:
        if settings.provider != "openrouter" and speech_transcriber is None:
            return {"available": False}
        transcriber = speech_transcriber or OpenRouterSpeechTranscriber(settings)
        try:
            return {"available": await transcriber.available()}
        except (httpx.HTTPError, ValueError):
            return {"available": False}

    @app.post("/speech/transcribe")
    async def transcribe_speech(request: Request, language: Literal["ar", "en"]) -> dict[str, str]:
        if request.headers.get("content-type", "").split(";", 1)[0] != "audio/webm":
            raise HTTPException(status_code=415, detail="WebM audio is required")
        content_length = request.headers.get("content-length", "0")
        if not content_length.isdecimal():
            raise HTTPException(status_code=400, detail="Invalid recording length")
        if int(content_length) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio recording is too large")
        audio = await request.body()
        if len(audio) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio recording is too large")
        if not audio.startswith(b"\x1a\x45\xdf\xa3"):
            raise HTTPException(status_code=400, detail="Invalid WebM recording")
        if settings.provider != "openrouter" and speech_transcriber is None:
            raise HTTPException(status_code=503, detail="Speech transcription is unavailable")
        transcriber = speech_transcriber or OpenRouterSpeechTranscriber(settings)
        try:
            return {"text": await transcriber.transcribe(audio, language)}
        except OpenRouterBudgetError as error:
            raise HTTPException(status_code=429, detail="Speech budget is unavailable") from error
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(status_code=502, detail="Speech transcription failed") from error

    if test_clock_enabled:

        @app.post("/__test/advance-time", status_code=204)
        async def advance_test_time(request: AdvanceTestTime) -> None:
            if not 0 < request.seconds <= 120:
                raise HTTPException(status_code=400, detail="Invalid test clock advance")
            clock_offset[0] += request.seconds

    @app.post("/step")
    async def step(request: StepRequest) -> dict[str, object]:
        if settings.provider != "scripted":
            raise HTTPException(status_code=404, detail="Use the live session API")
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
    async def create_session(
        http_request: Request, request: SessionCreate | None = None
    ) -> dict[str, str]:
        authority = http_request.state.browser_authority
        for existing in list(authority.sessions):
            try:
                sessions.get(existing)
            except SessionNotFound:
                authority.sessions.discard(existing)
        if len(authority.sessions) >= 8:
            raise HTTPException(status_code=429, detail="Too many active sessions")
        try:
            session = sessions.create(request.tab_id if request is not None else None)
        except OverflowError as error:
            raise HTTPException(status_code=503, detail="Session capacity reached") from error
        session.shopper = http_request.state.shopper
        authority.sessions.add(session.session_id)
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
        session_id: str,
        task_id: str,
        request: RetryRequest,
        x_tab_id: str | None = Header(default=None),
    ) -> dict[str, str]:
        try:
            task = sessions.retry_interpretation(session_id, task_id, x_tab_id, request.snapshot)
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
        return await session_event_response(sessions, session_id, request, after, once, tab_id)

    @app.post("/sessions/{session_id}/action-results", status_code=202)
    async def accept_action_result(
        session_id: str,
        action_result: ActionResult,
        x_tab_id: str | None = Header(default=None),
    ) -> dict[str, str]:
        try:
            task = sessions.accept_result(session_id, action_result, x_tab_id)
            if task.status == "interpreting" and task.model_call_id:
                await run_interpretation(session_id, task.task_id, task.model_call_id)
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[identity_settings["panel_origin"]],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    return app


app = create_app()
