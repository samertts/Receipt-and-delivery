"""Standard API response envelope for consistent response format.

All API responses use the format:
{
    "success": true|false,
    "message": "description",
    "data": ...,
    "meta": { ... }
}
"""

from typing import Any


def wrap_response(
    data: Any = None,
    meta: dict[str, Any] | None = None,
    success: bool = True,
    message: str = "",
) -> dict[str, Any]:
    import datetime
    return {
        "success": success,
        "message": message,
        "data": data,
        "meta": {
            "timestamp": datetime.datetime.now(
                datetime.timezone.utc,
            ).isoformat(),
            **(meta or {}),
        },
    }


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "",
) -> dict[str, Any]:
    return wrap_response(
        data=items,
        message=message,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        },
    )


def error_response(
    message: str = "",
    error_code: str = "UNKNOWN",
    status_code: int = 400,
    data: Any = None,
) -> dict[str, Any]:
    import datetime
    return {
        "success": False,
        "message": message,
        "data": data,
        "meta": {
            "error_code": error_code,
            "status_code": status_code,
            "timestamp": datetime.datetime.now(
                datetime.timezone.utc,
            ).isoformat(),
        },
    }



