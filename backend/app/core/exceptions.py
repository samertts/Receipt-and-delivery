from typing import Any, Optional

from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[dict[str, str]] = None,
        error_code: str = "UNKNOWN",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundError(AppException):
    def __init__(self, detail: str = "المورد غير موجود") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "غير مصرح به") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(AppException):
    def __init__(self, detail: str = "ليس لديك صلاحية لهذا الإجراء") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


class ValidationError(AppException):
    def __init__(self, detail: str = "بيانات غير صالحة") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )


class ConflictError(AppException):
    def __init__(self, detail: str = "مكرر - موجود مسبقاً") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
        )


class RateLimitError(AppException):
    def __init__(self, detail: str = "طلبات كثيرة - الرجاء المحاولة لاحقاً") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT",
        )
