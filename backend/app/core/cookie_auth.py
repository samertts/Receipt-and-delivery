"""HttpOnly cookie session helpers for the browser API.

The legacy ``/api/v1`` contract continues to support bearer tokens for the
 desktop/mobile synchronization clients. Browser requests under ``/api`` use
 HttpOnly access/refresh cookies and a readable CSRF cookie.
"""

from __future__ import annotations

import secrets
from typing import Mapping

from fastapi import Request, Response

from app.core.config import settings

ACCESS_COOKIE = "lab_access_token"
REFRESH_COOKIE = "lab_refresh_token"
CSRF_COOKIE = "lab_csrf_token"
CSRF_HEADER = "X-CSRF-Token"
COOKIE_PATH = "/api"


def is_browser_api_request(request: Request) -> bool:
    path = request.url.path
    return path.startswith("/api/") and not path.startswith("/api/v1/")


def cookie_secure(request: Request) -> bool:
    """Use Secure in deployed environments while keeping local HTTP usable."""
    if settings.environment.lower() in {"prod", "production", "staging"}:
        return True
    return request.url.scheme.lower() == "https"


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_session_cookies(
    response: Response,
    tokens: Mapping[str, str],
    request: Request,
) -> None:
    secure = cookie_secure(request)
    common = {
        "secure": secure,
        "httponly": True,
        "samesite": "lax",
        "path": COOKIE_PATH,
    }
    response.set_cookie(ACCESS_COOKIE, tokens["access_token"], max_age=60 * settings.access_token_expire_minutes, **common)
    response.set_cookie(REFRESH_COOKIE, tokens["refresh_token"], max_age=60 * 60 * 24 * settings.refresh_token_expire_days, **common)
    response.set_cookie(
        CSRF_COOKIE,
        new_csrf_token(),
        max_age=60 * 60 * 24 * settings.refresh_token_expire_days,
        secure=secure,
        httponly=False,
        samesite="lax",
        path=COOKIE_PATH,
    )


def clear_session_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path=COOKIE_PATH)


def request_token(
    request: Request,
    bearer_token: str | None,
    cookie_name: str = ACCESS_COOKIE,
) -> str:
    if bearer_token:
        return bearer_token
    if is_browser_api_request(request):
        return request.cookies.get(cookie_name, "")
    return ""
