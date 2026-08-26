"""Application errors and safe Arabic messages for desktop user interfaces."""

from __future__ import annotations

import logging
logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class AuthenticationError(AppError):
    pass


class AuthorizationError(AppError):
    pass


class SessionExpiredError(AppError):
    pass


class ValidationError(AppError):
    pass


def to_arabic_error(error: BaseException, context: str = "") -> str:
    """Log the technical exception and return a non-sensitive Arabic message."""
    logger.error("%s: %s", context or "application error", error, exc_info=True)
    message = str(error).lower()
    prefix = f"{context}: " if context else ""

    if isinstance(error, (AuthenticationError, SessionExpiredError)):
        return prefix + "انتهت الجلسة أو تعذر التحقق من بيانات الدخول. سجّل الدخول مرة أخرى."
    if isinstance(error, AuthorizationError):
        return prefix + "ليس لديك الصلاحية لتنفيذ هذا الإجراء."
    if isinstance(error, ValidationError) or "validation" in message:
        return prefix + "البيانات المدخلة غير صحيحة. راجع الحقول المطلوبة وحاول مرة أخرى."
    if isinstance(error, FileNotFoundError) or "no such file" in message or "not found" in message:
        return prefix + "الملف المطلوب غير موجود أو تم نقله."
    if isinstance(error, PermissionError) or "permission denied" in message or "access is denied" in message:
        return prefix + "لا يمكن الوصول إلى الملف أو المجلد. تحقق من الصلاحيات."
    if isinstance(error, OSError) and any(token in message for token in ("disk", "space", "read-only")):
        return prefix + "تعذر الحفظ بسبب مشكلة في القرص أو عدم كفاية المساحة."
    if "locked" in message or "busy" in message or "database is locked" in message:
        return prefix + "قاعدة البيانات مشغولة حاليًا. أغلق العمليات الأخرى وحاول مرة أخرى."
    if isinstance(error, (ConnectionError, TimeoutError)) or any(
        token in message for token in ("connection", "network", "timeout", "urlopen")
    ):
        return prefix + "تعذر الاتصال بالخدمة. تحقق من الشبكة وحاول مرة أخرى."
    if any(token in message for token in ("printer", "print", "spool", "qprinter")):
        return prefix + "تعذرت الطباعة. تحقق من اتصال الطابعة وإعداداتها."
    if isinstance(error, ValueError):
        return prefix + "القيمة المدخلة غير صالحة."
    return prefix + "حدث خطأ غير متوقع. تم تسجيل التفاصيل للمراجعة الآمنة."
