from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.auth.permissions import check_permission
from lab_system.app.audit.logger import log_action
from lab_system.app.services.desktop_settings_service import DesktopSettingsService
from lab_system.app.ui.notifications import toast
from lab_system.app.ui.page_header import PageHeader


class SettingsPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self._settings_svc = DesktopSettingsService()
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        header = PageHeader("إعدادات النظام", "تخصيص إعدادات التطبيق")
        self.layout().addWidget(header)

        header.add_action("حفظ الإعدادات", self._save)

        self.fields = {}
        form = QFormLayout()
        defaults = self._settings_svc.get_defaults()
        for key, default in defaults.items():
            inp = QLineEdit()
            inp.setText(self._settings_svc.get(key, default))
            self.fields[key] = inp
            form.addRow(self._label_for(key), inp)
        self.layout().addLayout(form)

    def _label_for(self, key: str) -> str:
        labels = {
            "receipt.numbering_prefix": "بادئة الترقيم",
            "receipt.font_size": "حجم الخط",
            "receipt.margin_mm": "الهامش (مم)",
            "receipt.template": "القالب",
            "printer.mode": "وضع الطباعة",
            "backup.auto_enabled": "نسخ احتياطي تلقائي",
            "backup.path": "مسار النسخ الاحتياطي",
            "backup.retention_max": "الحد الأقصى للنسخ",
            "session.timeout_minutes": "مهلة الجلسة (دقيقة)",
            "security.max_login_attempts": "محاولات تسجيل الدخول القصوى",
            "security.login_lockout_minutes": "مدة القفل (دقيقة)",
            "security.force_password_change_days": "إجبار تغيير كلمة المرور (يوم)",
        }
        return labels.get(key, key)

    def _save(self):
        check_permission(self.current_user, "settings.update")
        settings = {key: inp.text() for key, inp in self.fields.items()}
        self._settings_svc.set_all(settings)
        log_action(self.current_user["id"], "settings_updated", "تحديث إعدادات النظام")
        toast(self, "تم حفظ الإعدادات", "success")
