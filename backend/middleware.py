"""HTTP middleware for the Bazzar Terminal API (P5, roadmap 5.1–5.4).

Three small Starlette middlewares:

* :class:`RequestIDMiddleware` — generates (or forwards) an ``X-Request-ID``
  per request, binds it to the structlog context so every log line emitted
  while serving the request carries it, and returns the header.
* :class:`BearerAuthMiddleware` — when ``BAZZAR_API_TOKEN`` is set, every
  ``/api/*`` request must carry ``Authorization: Bearer <token>``; anything
  else gets a 401 in the standard error envelope. When the env var is unset
  (plain dev run) the API is open — a documented development fallback. The
  Kite Connect redirect callback is exempt: the external system browser is
  redirected there by kite.trade after login and cannot know the token (the
  one-time ``request_token`` is itself the credential).
* :class:`WeakETagMiddleware` — weak, body-hash ETags on the slow-changing
  JSON GET endpoints (indices / macro / benchmarks); answers ``304 Not
  Modified`` when ``If-None-Match`` matches, so the renderer's polls stay
  cheap.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Awaitable, Callable

import structlog.contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .settings import get_settings

# Paths that stay reachable without the bearer token even when one is set:
# the Kite redirect callback is hit by the *external* browser after the
# Zerodha login, which cannot carry the per-launch token.
PUBLIC_PATHS = frozenset({"/api/auth/kite/callback", "/api/v1/auth/kite/callback"})

# Path prefixes that get weak ETags (GET, JSON only — chart PNGs excluded).
_ETAG_PREFIXES = ("/api/indices", "/api/v1/indices", "/api/macro", "/api/v1/macro")
_ETAG_BENCH = re.compile(r"^/api(?:/v1)?/benchmarks/?$")


def error_envelope(code: str, message: str) -> dict[str, dict[str, str]]:
    """The single API error shape: ``{"error": {"code", "message"}}``."""
    return {"error": {"code": code, "message": message}}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach an ``X-Request-ID`` to every request and bind it to structlog."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
        response.headers["X-Request-ID"] = request_id
        return response


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Require ``Authorization: Bearer <BAZZAR_API_TOKEN>`` on /api/* when set."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        token = get_settings().bazzar_api_token
        path = request.url.path
        if token and path.startswith("/api/") and path not in PUBLIC_PATHS:
            if request.headers.get("authorization") != f"Bearer {token}":
                return JSONResponse(
                    status_code=401,
                    content=error_envelope("unauthorized", "missing or invalid bearer token"),
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return await call_next(request)


class WeakETagMiddleware(BaseHTTPMiddleware):
    """Weak body-hash ETag + If-None-Match → 304 on the slow-changing GETs."""

    @staticmethod
    def _eligible(request: Request) -> bool:
        if request.method != "GET":
            return False
        path = request.url.path
        if path.endswith(".png"):
            return False
        return path.startswith(_ETAG_PREFIXES) or bool(_ETAG_BENCH.match(path))

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self._eligible(request):
            return await call_next(request)
        response = await call_next(request)
        if response.status_code != 200 or "application/json" not in response.headers.get(
            "content-type", ""
        ):
            return response
        body = b""
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body += chunk if isinstance(chunk, bytes) else chunk.encode()
        etag = f'W/"{hashlib.sha256(body).hexdigest()[:32]}"'
        offered = request.headers.get("if-none-match", "")
        if etag in [tag.strip() for tag in offered.split(",")]:
            return Response(status_code=304, headers={"ETag": etag})
        headers = dict(response.headers)
        headers["ETag"] = etag
        return Response(content=body, status_code=200, headers=headers)
