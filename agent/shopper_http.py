"""HTTP authority boundary shared by all Agent routes, including streaming delivery."""

import secrets

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from agent.session_state import SessionExpired, SessionNotFound
from agent.sessions import SessionStore
from agent.shopper_access import ShopperAccess
from agent.storefront_service import StorefrontService


def install_shopper_http(
    app: FastAPI,
    sessions: SessionStore,
    service: StorefrontService,
    *,
    panel_origin: str,
    evaluation: bool,
) -> None:
    access = ShopperAccess()
    app.state.shopper_access = access
    app.state.storefront_service = service

    async def alive(record) -> bool:
        if record.shopper is None:
            return False
        try:
            return await app.state.storefront_service.validate(record.shopper)
        except Exception:
            return False

    @app.middleware("http")
    async def authorize(request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or path == "/health":
            return await call_next(request)
        if (path.startswith("/__test/") or path == "/step") and not evaluation:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        cookie_values = [
            part.strip().split("=", 1)[1]
            for part in request.headers.get("cookie", "").split(";")
            if part.strip().startswith("copilot_agent=")
        ]
        credential = cookie_values[0] if len(cookie_values) == 1 else ""
        record = access.resolve(credential)
        new_cookie = None
        if path == "/shopper/bootstrap" and request.method == "POST":
            if request.headers.get("origin") != panel_origin:
                return JSONResponse({"detail": "Invalid origin"}, status_code=403)
            if record is None:
                try:
                    new_cookie, record = access.create()
                except OverflowError:
                    return JSONResponse({"detail": "Capacity reached"}, status_code=503)
            result = JSONResponse({"csrf": record.csrf})
            if new_cookie:
                result.set_cookie(
                    "copilot_agent",
                    new_cookie,
                    httponly=True,
                    secure=panel_origin.startswith("https:"),
                    samesite="strict",
                    path="/",
                )
            result.headers["Cache-Control"] = "no-store"
            return result
        if record is None:
            return JSONResponse({"detail": "Shopper identity required"}, status_code=401)
        if request.method not in {"GET", "HEAD"} and (
            request.headers.get("origin") != panel_origin
            or not secrets.compare_digest(request.headers.get("x-csrf-token", ""), record.csrf)
        ):
            return JSONResponse({"detail": "Invalid browser authority"}, status_code=403)
        if path == "/shopper/challenge" and request.method == "POST":
            try:
                result = JSONResponse({"challenge": access.challenge(record)})
            except OverflowError:
                return JSONResponse({"detail": "Too many pending links"}, status_code=429)
            result.headers["Cache-Control"] = "no-store"
            return result
        if path == "/shopper/link" and request.method == "POST":
            try:
                payload = await request.json()
                challenge, ticket = payload["challenge"], payload["ticket"]
                if (
                    not isinstance(challenge, str)
                    or not isinstance(ticket, str)
                    or len(ticket) != 64
                ):
                    raise ValueError()
                if not access.consume_challenge(record, challenge):
                    raise ValueError()
                binding = await app.state.storefront_service.redeem(ticket, challenge)
                if record.shopper is not None and record.shopper != binding:
                    # A changed Storefront identity requires discarding old task references.
                    record.sessions.clear()
                    record.shopper = None
                    result = JSONResponse(
                        {"detail": "Storefront reset; reload to link again"}, status_code=409
                    )
                else:
                    record.shopper = binding
                    result = JSONResponse({"linked": True, "shopper_context": binding.context})
            except Exception:
                result = JSONResponse({"detail": "Shopper linking failed"}, status_code=409)
            result.headers["Cache-Control"] = "no-store"
            return result
        if not await alive(record):
            return JSONResponse(
                {"detail": "Storefront identity expired or unavailable"}, status_code=401
            )
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "sessions":
            if parts[1] not in record.sessions:
                return JSONResponse({"detail": "Session not found"}, status_code=404)
            try:
                session = sessions.get(parts[1])
                if session.shopper != record.shopper or parts[1] not in record.sessions:
                    raise SessionNotFound(parts[1])
            except SessionExpired:
                return JSONResponse({"detail": "Session expired"}, status_code=410)
            except SessionNotFound:
                return JSONResponse({"detail": "Session not found"}, status_code=404)
        access.resolve(credential, touch=True)
        request.state.shopper = record.shopper
        request.state.browser_authority = record
        bound_shopper = record.shopper

        async def still_authorized():
            if access.resolve(credential) is not record or record.shopper != bound_shopper:
                return False
            valid = await alive(record)
            return valid and record.shopper == bound_shopper

        request.state.shopper_authorized = still_authorized
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response
