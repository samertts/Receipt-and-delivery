import re
from typing import Optional

from lab_system.app.utils.errors import ValidationError

PASSWORD_MIN_LENGTH = 8


def validate_password(password: str) -> Optional[str]:
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"كلمة المرور يجب أن تكون على الأقل {PASSWORD_MIN_LENGTH} محارف"
    if not re.search(r"[a-z]", password):
        return "يجب أن تحتوي كلمة المرور على حرف إنجليزي صغير"
    if not re.search(r"[A-Z]", password):
        return "يجب أن تحتوي كلمة المرور على حرف إنجليزي كبير"
    if not re.search(r"\d", password):
        return "يجب أن تحتوي كلمة المرور على رقم"
    if not re.search(r"[@$!%*#?&_]", password):
        return "يجب أن تحتوي كلمة المرور على رمز خاص (@$!%*#?&_)"
    return None


def validate_required(value: str, field_name: str = "") -> None:
    if not value or not value.strip():
        raise ValidationError(f"حقل {field_name} مطلوب")


def validate_username(username: str) -> Optional[str]:
    if len(username) < 3:
        return "اسم المستخدم يجب أن يكون 3 محارف على الأقل"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return "اسم المستخدم يمكن أن يحتوي فقط على حروف وأرقام و _"
    return None
