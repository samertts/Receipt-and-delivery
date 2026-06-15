"""Standard API response envelope for consistent response format.

All responses are wrapped in:
{
    "data": ...,
    "meta": {
        "page": ...,
        "per_page": ...,
        "total": ...,
        "timestamp": "..."
    }
}
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def wrap_response(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "meta": {
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            **(meta or {}),
        },
    }


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    per_page: int,
) -> dict[str, Any]:
    return wrap_response(
        data=items,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        },
    )


async def response_envelope_middleware(request: Request, call_next):
    """FastAPI middleware that wraps list responses in the standard envelope."""

    response = await call_next(request)

    # Skip error responses, streaming, and non-JSON
    if response.status_code >= 400:
        return response
    content_type = response.headers.get("content-type", "")
    if "json" not in content_type:
        return response

    # Only wrap GET list endpoints (no path param at the end)
    path = request.url.path
    if request.method != "GET":
        return response
    if path in ("/api/docs", "/api/redoc", "/api/openapi.json", "/api/health"):
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    if not body:
        return response

    import json

    try:
        data = json.loads(body)
        # Don't double-wrap
        if isinstance(data, dict) and "data" in data and "meta" in data:
            return JSONResponse(content=data, status_code=response.status_code)
        # Only wrap arrays (list endpoints)
        if not isinstance(data, list):
            return JSONResponse(content=data, status_code=response.status_code)
        wrapped = wrap_response(data)
        return JSONResponse(content=wrapped, status_code=response.status_code)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return response
