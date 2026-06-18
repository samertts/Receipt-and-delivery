from datetime import datetime
from importlib.metadata import version as _pkg_version

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal

router = APIRouter(prefix="/health", tags=["health"])


def _check_db() -> tuple[bool, str | None]:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True, None
    except Exception as e:
        logger.warning(f"Health check DB error: {e}")
        return False, str(e)


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


@router.get("")
def health():
    db_ok, db_detail = _check_db()
    checks = {
        "app": {"status": "ok", "name": settings.app_name, "version": settings.app_version},
        "database": {"status": "ok" if db_ok else "error", "detail": db_detail},
        "timestamp": _utcnow(),
    }
    overall = all(v.get("status") == "ok" for v in checks.values() if isinstance(v, dict))
    return {
        "status": "ok" if overall else "degraded",
        "checks": checks,
    }


health.__exclude_from_envelope__ = True


@router.get("/live")
def liveness():
    return {"status": "alive", "timestamp": _utcnow()}


liveness.__exclude_from_envelope__ = True


@router.get("/ready")
def readiness():
    db_ok, db_detail = _check_db()
    if not db_ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database unreachable", "detail": db_detail},
        )
    return {
        "status": "ready",
        "database": "connected",
        "version": settings.app_version,
        "timestamp": _utcnow(),
    }


readiness.__exclude_from_envelope__ = True


@router.get("/version")
def version():
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "timestamp": _utcnow(),
    }


version.__exclude_from_envelope__ = True


@router.get("/dependencies")
def dependencies():
    deps = []
    db_ok, db_detail = _check_db()
    deps.append({
        "name": "database",
        "status": "connected" if db_ok else "disconnected",
        "detail": db_detail,
        "required": True,
    })
    deps.append({
        "name": "secret_key",
        "status": "configured" if settings.effective_secret_key else "missing",
        "detail": None,
        "required": True,
    })
    deps.append({
        "name": "storage",
        "status": "available",
        "detail": None,
        "required": False,
    })
    all_ok = all(d["status"] in ("connected", "configured", "available") for d in deps)
    return {
        "status": "healthy" if all_ok else "degraded",
        "dependencies": deps,
        "timestamp": _utcnow(),
    }


dependencies.__exclude_from_envelope__ = True
