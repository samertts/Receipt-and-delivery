from datetime import datetime

from lab_system.app.database import db as _db
from lab_system.app.services.base_service import BaseService
from lab_system.app.services.user_service import (
    authenticate,
    get_recent_failures,
    needs_password_change,
)
from lab_system.app.utils.errors import AuthenticationError


class AuthService(BaseService):
    def __init__(self):
        self._session_user = None
        self._login_time = None
        self._last_activity = None

    def login(self, username: str, password: str):
        max_attempts = self._get_setting('security.max_login_attempts', '5')
        lockout_minutes = self._get_setting('security.login_lockout_minutes', '5')
        failures = get_recent_failures(username, int(lockout_minutes))
        if failures >= int(max_attempts):
            raise AuthenticationError(
                f'تم تجاوز عدد محاولات الدخول المسموح بها. حاول بعد {lockout_minutes} دقائق'
            )
        user = authenticate(username, password)
        if not user:
            raise AuthenticationError('بيانات الدخول غير صحيحة')
        self._session_user = dict(user)
        self._login_time = datetime.now()
        self._last_activity = datetime.now()
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
            raise AuthenticationError('الرجاء تسجيل الدخول أولاً')
        timeout_minutes = int(self._get_setting('session.timeout_minutes', '15'))
        if timeout_minutes > 0:
            elapsed = (datetime.now() - self._last_activity).total_seconds() / 60
            if elapsed > timeout_minutes:
                self.logout()
                from lab_system.app.utils.errors import SessionExpiredError
                raise SessionExpiredError('انتهت صلاحية الجلسة. الرجاء تسجيل الدخول مرة أخرى')
        self.touch_activity()

    def logout(self) -> None:
        self._session_user = None
        self._login_time = None
        self._last_activity = None

    def needs_password_change(self) -> bool:
        if not self._session_user:
            return False
        return needs_password_change(self._session_user)

    def change_password(self, old_password: str, new_password: str) -> None:
        from lab_system.app.services.user_service import change_password as _change_password
        if not self._session_user:
            raise AuthenticationError('الرجاء تسجيل الدخول أولاً')
        _change_password(self._session_user['id'], old_password, new_password)
        self._session_user['password_changed_at'] = datetime.now().isoformat(timespec='seconds')

    def _get_setting(self, key: str, default: str) -> str:
        with _db.get_conn() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row['value'] if row else default
