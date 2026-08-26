from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.auth.permissions import check_permission
from lab_system.app.audit.logger import log_action
from lab_system.app.services.desktop_settings_service import DesktopSettingsService
from lab_system.app.services.receipt_branding_service import ReceiptBrandingService
from lab_system.app.ui.notifications import toast
from lab_system.app.ui.page_header import PageHeader
from lab_system.app.utils.errors import to_arabic_error


class SettingsPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self._settings_svc = DesktopSettingsService()
        self._branding_svc = ReceiptBrandingService()
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

        branding_form = QFormLayout()
        branding = self._branding_svc.load()
        self.branding_fields = {}
        for key, label in (
            ("company_name", "اسم الشركة في الإيصال"),
            ("subtitle", "العنوان الفرعي"),
            ("footer", "تذييل الإيصال"),
            ("primary_color", "اللون الرئيسي (#RRGGBB)"),
        ):
            inp = QLineEdit(str(branding.get(key, "")))
            self.branding_fields[key] = inp
            branding_form.addRow(label, inp)

        logo_row = QHBoxLayout()
        logo_input = QLineEdit(str(branding.get("logo_path", "")))
        logo_input.setReadOnly(True)
        self.branding_fields["logo_path"] = logo_input
        browse_logo = QPushButton("اختيار صورة")
        browse_logo.clicked.connect(self._choose_logo)
        logo_row.addWidget(logo_input, 1)
        logo_row.addWidget(browse_logo)
        branding_form.addRow("شعار الشركة (PNG/JPEG)", logo_row)

        layout_input = QComboBox()
        layout_input.addItem("A4 — نسخة واحدة", "a4")
        layout_input.addItem("A5 — نسخة واحدة", "a5")
        layout_input.addItem("A4 — نسختان مستلم/مرسل", "a4-two-up")
        selected_layout = branding.get("layout", "a4")
        selected_index = max(0, layout_input.findData(selected_layout))
        layout_input.setCurrentIndex(selected_index)
        self.branding_fields["layout"] = layout_input
        branding_form.addRow("التخطيط الافتراضي", layout_input)
        self.layout().addWidget(PageHeader("هوية الإيصال", "تخصيص الشعار والنص والتخطيط الافتراضي"))
        self.layout().addLayout(branding_form)

    def _choose_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار شعار الشركة",
            "",
            "صور PNG أو JPEG (*.png *.jpg *.jpeg)",
        )
        if path:
            self.branding_fields["logo_path"].setText(path)

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
        try:
            check_permission(self.current_user, "settings.update")
            settings = {key: inp.text() for key, inp in self.fields.items()}
            self._settings_svc.set_all(settings)
            branding_values = {
                key: field.currentData() if isinstance(field, QComboBox) else field.text()
                for key, field in self.branding_fields.items()
            }
            self._branding_svc.save(branding_values)
            log_action(self.current_user["id"], "settings_updated", "تحديث إعدادات النظام وهوية الإيصال")
            toast(self, "تم حفظ الإعدادات وهوية الإيصال", "success")
        except Exception as exc:
            QMessageBox.warning(self, "تعذر الحفظ", to_arabic_error(exc, "حفظ الإعدادات"))
