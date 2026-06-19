from contextlib import asynccontextmanager
from typing import Callable, Awaitable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    audit,
    auth,
    attachments,
    health,
    organizations,
    reports,
    sync,
    transactions,
    users,
)
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger, setup_logging
from app.core.response_envelope import wrap_response, error_response
from app.core.security import rate_limit_middleware


ENVELOPE_EXCLUDE_PATHS = {
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/health",
    "/api/health/live",
    "/api/health/ready",
    "/api/health/version",
    "/api/health/dependencies",
    "/api/v1/health",
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/api/v1/health/version",
    "/api/v1/health/dependencies",
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging(level=settings.log_level)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    if "lab_user:lab_pass" in settings.database_url:
        logger.warning(
            "Default database credentials detected in database_url. "
            "Change them before deploying to production."
        )
    try:
        from app.services.auth_service import AuthService
        from app.db.session import SessionLocal

        db = SessionLocal()
        purged = AuthService.purge_expired_blacklisted_tokens(db)
        if purged:
            logger.info(f"Purged {purged} expired blacklisted tokens")
        db.close()
    except Exception as exc:
        logger.warning(f"Could not purge expired tokens on startup: {exc}")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

app.middleware("http")(rate_limit_middleware)


@app.middleware("http")
async def response_envelope_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    if response.status_code >= 400:
        return response
    path = request.url.path
    if path in ENVELOPE_EXCLUDE_PATHS:
        return response
    ct = response.headers.get("content-type", "")
    if "json" not in ct:
        return response
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    if not body:
        return response
    import json

    try:
        data = json.loads(body)
        if isinstance(data, dict) and "success" in data and "meta" in data:
            return JSONResponse(content=data, status_code=response.status_code)
        wrapped = wrap_response(data=data)
        return JSONResponse(content=wrapped, status_code=response.status_code)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        f"App exception: {exc.error_code} - {exc.detail}",
        extra={"path": request.url.path, "error_code": exc.error_code},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            error_code=exc.error_code,
            status_code=exc.status_code,
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"path": request.url.path},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="خطأ داخلي في الخادم",
            error_code="INTERNAL_ERROR",
            status_code=500,
        ),
    )


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(attachments.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api")
app.include_router(health.router, prefix="/api/v1")
