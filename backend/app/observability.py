"""Lightweight request correlation and structured HTTP logging."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger("team_project.http")


def _request_id(request: Request) -> str:
    candidate = request.headers.get("x-request-id", "").strip()
    if candidate and len(candidate) <= 128 and all(31 < ord(char) < 127 for char in candidate):
        return candidate
    return uuid.uuid4().hex


async def request_observability(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a request ID and emit one structured JSON log entry per request."""
    request_id = _request_id(request)
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception(
            json.dumps(
                {
                    "event": "http_request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
                separators=(",", ":"),
            )
        )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
            separators=(",", ":"),
        )
    )
    return response
