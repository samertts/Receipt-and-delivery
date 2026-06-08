from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.auth.permissions import check_permission
from lab_system.app.audit.logger import log_action
from lab_system.app.database.db import DEFAULT_SETTINGS, get_conn
from lab_system.app.ui.notifications import toast
from lab_system.app.ui.page_header import PageHeader


class SettingsPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        header = PageHeader("إعدادات النظام", "تخصيص إعدادات التطبيق")
        self.layout().addWidget(header)

        header.add_action("حفظ الإعدادات", self._save)

        self.fields = {}
        form = QFormLayout()
        for key, default in DEFAULT_SETTINGS.items():
            inp = QLineEdit()
            inp.setText(self._get_setting(key, default))
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

    def _get_setting(self, key: str, default: str) -> str:
        with get_conn() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default

    def _save(self):
        check_permission(self.current_user, 'settings.update')
        with get_conn() as conn:
            for key, inp in self.fields.items():
                conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, inp.text()))
        log_action(self.current_user["id"], "settings_updated", "تحديث إعدادات النظام")
        toast(self, "تم حفظ الإعدادات", "success")
