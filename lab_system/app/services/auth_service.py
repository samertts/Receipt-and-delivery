from datetime import datetime

from lab_system.app.database import db as _db
from lab_system.app.services.base_service import BaseService
from lab_system.app.services.user_service import (
    authenticate,
    needs_password_change,
)
from lab_system.app.utils.errors import AuthenticationError


class AuthService(BaseService):
    def __init__(self):
        self._session_user = None
        self._login_time = None
        self._last_activity = None
        self._last_sensitive_auth = None

    def login(self, username: str, password: str):
        max_attempts = int(self._get_setting("security.max_login_attempts", "5"))
        lockout_minutes = int(self._get_setting("security.login_lockout_minutes", "5"))
        user = authenticate(username, password, max_attempts, lockout_minutes)
        if not user:
            raise AuthenticationError("بيانات الدخول غير صحيحة")
        self._session_user = dict(user)
        self._login_time = datetime.now()
        self._last_activity = datetime.now()
        self._last_sensitive_auth = None
        return self._session_user

    @property
    def is_logged_in(self) -> bool:
        return self._session_user is not None

    @property
    def current_user(self) -> dict | None:
        return self._session_user

    def touch_activity(self) -> None:
        self._last_activity = datetime.now()

    def check_session(self) -> None:
        if not self._session_user:
            raise AuthenticationError("الرجاء تسجيل الدخول أولاً")
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT status, password_changed_at FROM users WHERE id=?",
                (self._session_user["id"],),
            ).fetchone()
        if not row or row["status"] != "Active":
            self.logout()
            raise AuthenticationError("تم تعطيل الحساب. الرجاء التواصل مع المشرف")
        if row["password_changed_at"] != self._session_user.get(
            "password_changed_at", ""
        ):
            self.logout()
            raise AuthenticationError(
                "تم تغيير كلمة المرور. الرجاء تسجيل الدخول مرة أخرى"
            )
        timeout_minutes = int(self._get_setting("session.timeout_minutes", "15"))
        if timeout_minutes > 0:
            elapsed = (datetime.now() - self._last_activity).total_seconds() / 60
            if elapsed > timeout_minutes:
                self.logout()
                from lab_system.app.utils.errors import SessionExpiredError

                raise SessionExpiredError(
                    "انتهت صلاحية الجلسة. الرجاء تسجيل الدخول مرة أخرى"
                )
        self.touch_activity()

    def reauthenticate(self, password: str) -> bool:
        """Require the current password before a high-risk local operation."""
        if not self._session_user:
            raise AuthenticationError("الرجاء تسجيل الدخول أولاً")
        self.check_session()
        max_attempts = int(self._get_setting("security.max_login_attempts", "5"))
        lockout_minutes = int(self._get_setting("security.login_lockout_minutes", "5"))
        verified = authenticate(
            self._session_user["username"],
            password,
            max_attempts,
            lockout_minutes,
        )
        if not verified:
            raise AuthenticationError("إعادة التحقق مطلوبة قبل تنفيذ العملية الحساسة")
        self._last_sensitive_auth = datetime.now()
        self.touch_activity()
        return True

    def require_recent_reauthentication(self, max_age_minutes: int = 5) -> None:
        """Reject a sensitive operation unless password was recently re-entered."""
        if max_age_minutes <= 0:
            raise ValueError("max_age_minutes must be positive")
        if not self._session_user:
            raise AuthenticationError("الرجاء تسجيل الدخول أولاً")
        self.check_session()
        if not self._last_sensitive_auth:
            raise AuthenticationError("إعادة التحقق مطلوبة: أعد إدخال كلمة المرور قبل تنفيذ العملية الحساسة")
        elapsed = (datetime.now() - self._last_sensitive_auth).total_seconds() / 60
        if elapsed > max_age_minutes:
            self._last_sensitive_auth = None
            raise AuthenticationError("انتهت صلاحية إعادة التحقق للعملية الحساسة")

    def logout(self) -> None:
        self._session_user = None
        self._login_time = None
        self._last_activity = None
        self._last_sensitive_auth = None

    def needs_password_change(self) -> bool:
        if not self._session_user:
            return False
        return needs_password_change(self._session_user)

    def change_password(self, old_password: str, new_password: str) -> None:
        from lab_system.app.services.user_service import (
            change_password as _change_password,
        )

        if not self._session_user:
            raise AuthenticationError("الرجاء تسجيل الدخول أولاً")
        _change_password(self._session_user["id"], old_password, new_password)
        self._session_user["password_changed_at"] = datetime.now().isoformat(
            timespec="seconds"
        )

    def _get_setting(self, key: str, default: str) -> str:
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key=?", (key,)
            ).fetchone()
            return row["value"] if row else default
