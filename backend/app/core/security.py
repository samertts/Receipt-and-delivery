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


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        if len(self.requests[key]) >= self.max_requests:
            return True
        self.requests[key].append(now)
        return False


login_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
api_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


async def rate_limit_middleware(request: Request, call_next):
    # Disable rate limiting in test mode
    if os.environ.get("TESTING") or settings.debug:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    if "/auth/login" in request.url.path:
        if login_rate_limiter.is_rate_limited(client_ip):
            logger.warning(
                "Rate limit exceeded", extra={"ip_address": client_ip, "path": request.url.path},
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
