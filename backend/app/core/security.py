import os
import re
import time
from collections import defaultdict
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from fastapi import Request
from fastapi.responses import JSONResponse

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def validate_password_strength(password: str) -> Optional[str]:
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"كلمة المرور يجب أن تكون على الأقل {PASSWORD_MIN_LENGTH} محارف"
    if len(password) > PASSWORD_MAX_LENGTH:
        return f"كلمة المرور يجب أن تكون أقل من {PASSWORD_MAX_LENGTH} محرف"
    if not re.search(r"[a-z]", password):
        return "كلمة المرور يجب أن تحتوي على حرف صغير على الأقل"
    if not re.search(r"[A-Z]", password):
        return "كلمة المرور يجب أن تحتوي على حرف كبير على الأقل"
    if not re.search(r"\d", password):
        return "كلمة المرور يجب أن تحتوي على رقم على الأقل"
    if not re.search(r"[@$!%*#?&_]", password):
        return "كلمة المرور يجب أن تحتوي على رمز خاص على الأقل (@$!%*#?&_)"
    return None


class MemoryRateLimiter:
    """
    SECURITY NOTE: Rate limiter state is lost on restart.
    TODO: Implement Redis-backed or database-backed rate limiting for production.
    For now, the in-memory limiter provides basic protection.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._cleanup_counter = 0

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        self.requests[key] = [
            t for t in self.requests[key] if now - t < self.window_seconds
        ]

        # Periodic cleanup every 1000 requests
        self._cleanup_counter += 1
        if self._cleanup_counter >= 1000:
            self._cleanup_counter = 0
            cutoff = now - self.window_seconds
            self.requests = {
                k: v for k, v in self.requests.items() if v and v[-1] > cutoff
            }

        if len(self.requests[key]) >= self.max_requests:
            return True
        self.requests[key].append(now)
        return False


class RedisRateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis = None

    def _ensure_redis(self):
        if self._redis is None:
            try:
                import redis as _redis

                redis_url = (
                    settings.redis_url
                    if hasattr(settings, "redis_url")
                    else "redis://localhost:6379/0"
                )
                self._redis = _redis.from_url(redis_url, decode_responses=True)
            except ImportError:
                logger.warning(
                    "redis package not installed, falling back to in-memory rate limiter"
                )
                return False
            except Exception as e:
                logger.warning(
                    f"Redis connection failed: {e}, falling back to in-memory rate limiter"
                )
                return False
        return True

    def is_rate_limited(self, key: str) -> bool:
        if not self._ensure_redis():
            return fallback_limiter.is_rate_limited(key)
        try:
            pipe = self._redis.pipeline()
            now = int(time.time())
            window_start = now - self.window_seconds
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds)
            _, count, _ = pipe.execute()
            if count >= self.max_requests:
                return True
            self._redis.zadd(key, {str(now): now})
            return False
        except Exception as e:
            logger.warning(f"Redis rate limiter error: {e}, falling back to in-memory")
            return fallback_limiter.is_rate_limited(key)


fallback_limiter = MemoryRateLimiter(max_requests=10, window_seconds=60)
login_rate_limiter = MemoryRateLimiter(max_requests=5, window_seconds=60)
api_rate_limiter = MemoryRateLimiter(max_requests=100, window_seconds=60)

try:
    redis_url = getattr(settings, "redis_url", "")
    if redis_url:
        login_rate_limiter = RedisRateLimiter(
            max_requests=settings.rate_limit_login_max,
            window_seconds=settings.rate_limit_login_window,
        )
        api_rate_limiter = RedisRateLimiter(
            max_requests=settings.rate_limit_api_max,
            window_seconds=settings.rate_limit_api_window,
        )
        logger.info("Using Redis-backed rate limiter")
except (ImportError, Exception) as e:
    logger.info(f"Using in-memory rate limiter ({e})")


async def rate_limit_middleware(request: Request, call_next):
    if os.environ.get("RATE_LIMIT_DISABLED"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    if "/auth/login" in request.url.path:
        if login_rate_limiter.is_rate_limited(client_ip):
            logger.warning(
                "Rate limit exceeded",
                extra={"ip_address": client_ip, "path": request.url.path},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "طلبات كثيرة - الرجاء المحاولة لاحقاً",
                    "error_code": "RATE_LIMIT",
                },
            )
    elif api_rate_limiter.is_rate_limited(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "طلبات كثيرة - الرجاء المحاولة لاحقاً",
                "error_code": "RATE_LIMIT",
            },
        )

    response = await call_next(request)
    return response
