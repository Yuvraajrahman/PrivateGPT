from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import HTTPException, Request, WebSocket, status


def _get_presented_api_key_from_headers(headers) -> str | None:
    auth = headers.get("authorization")
    if auth:
        parts = auth.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
            return parts[1].strip()
    x = headers.get("x-api-key")
    if x and x.strip():
        return x.strip()
    return None


def require_api_key(request: Request) -> None:
    settings = request.app.state.settings
    api_key = getattr(settings, "rag_api_key", None)
    if not api_key:
        raise RuntimeError(
            "RAG_API_KEY is not set. Refusing to start without authentication enabled."
        )

    presented = _get_presented_api_key_from_headers(request.headers)
    if presented != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


async def require_api_key_websocket(websocket: WebSocket, request: Request) -> None:
    settings = request.app.state.settings
    api_key = getattr(settings, "rag_api_key", None)
    if not api_key:
        raise RuntimeError(
            "RAG_API_KEY is not set. Refusing to start without authentication enabled."
        )

    presented = _get_presented_api_key_from_headers(websocket.headers)
    if presented != api_key:
        await websocket.close(code=4401)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@dataclass
class FixedWindowRateLimiter:
    window_seconds: int
    max_requests: int

    def __post_init__(self) -> None:
        self._buckets: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        start, count = self._buckets.get(key, (now, 0))
        if now - start >= self.window_seconds:
            start, count = now, 0
        count += 1
        self._buckets[key] = (start, count)
        return count <= self.max_requests


def get_client_ip(request: Request) -> str:
    # If you put this behind a tunnel/proxy, you should configure trusted headers
    # and parse X-Forwarded-For safely. We intentionally keep this minimal.
    return request.client.host if request.client else "unknown"


def enforce_content_length(request: Request, max_bytes: int) -> None:
    cl = request.headers.get("content-length")
    if not cl:
        return
    try:
        n = int(cl)
    except ValueError:
        return
    if n > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload too large (max {max_bytes} bytes).",
        )

