from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.audit.logger import log_action
from lab_system.app.auth.permissions import check_permission
from lab_system.app.database.db import init_db
from lab_system.app.utils.validators import validate_password as _validate_password
from lab_system.app.diagnostics.startup import (
    diagnose_and_report,
    run_all_checks,
    self_repair,
)
from lab_system.app.services.auth_service import AuthService
from lab_system.app.services.catalog_service import seed_defaults
from lab_system.app.services.seed_service import seed_organizations
from lab_system.app.services.user_service import seed_default_users
from lab_system.app.ui.audit_page import AuditPage
from lab_system.app.ui.backup_page import BackupPage
from lab_system.app.ui.org_page import OrgPage
from lab_system.app.ui.receipts_page import ReceiptsPage
from lab_system.app.ui.reports_page import ReportsPage
from lab_system.app.ui.settings_page import SettingsPage
from lab_system.app.ui.users_page import UsersPage
from lab_system.app.utils.constants import APP_NAME, DEFAULT_WINDOW_SIZE, THEME
from lab_system.app.utils.errors import AuthenticationError, SessionExpiredError

SESSION_CHECK_INTERVAL = 30000


class ChangePasswordDialog(QDialog):
    def __init__(self, auth_service):
        super().__init__()
        self.auth = auth_service
        self.setWindowTitle("تغيير كلمة المرور")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFixedWidth(420)
        layout = QFormLayout(self)
        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        layout.addRow("كلمة المرور الحالية:", self.old_password)
        layout.addRow("كلمة المرور الجديدة:", self.new_password)
        layout.addRow("تأكيد كلمة المرور:", self.confirm_password)
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self._save)
        layout.addRow(save_btn)

    def _save(self):
        if self.new_password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "خطأ", "كلمتا المرور غير متطابقتين")
            return
        pwd_error = _validate_password(self.new_password.text())
        if pwd_error:
            QMessageBox.warning(self, "خطأ", pwd_error)
            return
        try:
            self.auth.change_password(self.old_password.text(), self.new_password.text())
            QMessageBox.information(self, "نجاح", "تم تغيير كلمة المرور بنجاح")
            self.accept()
        except AuthenticationError as e:
            QMessageBox.warning(self, "خطأ", str(e))
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تغيير كلمة المرور: {e}")


class LoginWindow(QDialog):
    def __init__(self, auth_service=None) -> None:
        super().__init__()
        self.user = None
        self.auth = auth_service or AuthService()
        self.setWindowTitle("تسجيل الدخول")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size:18px;font-weight:700;")
        self.username = QLineEdit()
        self.username.setPlaceholderText("اسم المستخدم")
        self.password = QLineEdit()
        self.password.setPlaceholderText("كلمة المرور")
        self.password.setEchoMode(QLineEdit.Password)
        submit = QPushButton("دخول")
        submit.clicked.connect(self._login)

        layout.addWidget(title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(submit)

    def _login(self) -> None:
        try:
            self.user = self.auth.login(
                self.username.text().strip(), self.password.text(),
            )
            log_action(self.user["id"], "login_success", "desktop_login")
            self.accept()
        except AuthenticationError as exc:
            QMessageBox.warning(self, "خطأ", str(exc))
        except Exception as exc:
            log_action("unknown", "login_error", str(exc))
            QMessageBox.warning(self, "خطأ", f"حدث خطأ غير متوقع: {exc}")


class DashboardPage(QWidget):
    def __init__(self, user, auth_service=None) -> None:
        super().__init__()
        self._auth = auth_service
        layout = QVBoxLayout(self)

        header = QLabel(f"مرحباً {user['full_name']}")
        header.setStyleSheet("font-size:18px;font-weight:700;")
        layout.addWidget(header)

        role_ar = {'Admin': 'مدير النظام', 'Supervisor': 'مشرف', 'User': 'مستخدم', 'Auditor': 'مدقق'}
        layout.addWidget(QLabel(f"الصلاحية: {role_ar.get(user['role'], user['role'])}"))
        layout.addWidget(QLabel("نظام إدارة الاستلام المختبري - الإصدار 1.0.0"))

        diag = run_all_checks()
        status = QLabel()
        if diag["all_ok"]:
            status.setText("✓ جميع الأنظمة تعمل بشكل طبيعي")
            status.setStyleSheet("color: green; font-weight: bold;")
        else:
            status.setText("⚠ توجد مشكلات في النظام — راجع سجل التشخيص")
            status.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(status)

        if self._auth and self._auth.needs_password_change():
            warn = QLabel("⚠ يرجى تغيير كلمة المرور الافتراضية")
            warn.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            layout.addWidget(warn)


class MainWindow(QMainWindow):
    def __init__(self, user, auth_service=None) -> None:
        super().__init__()
        self.user = user
        self.auth = auth_service or AuthService()
        self.setWindowTitle(APP_NAME)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setLayoutDirection(Qt.RightToLeft)

        root = QWidget()
        shell = QHBoxLayout(root)

        sidebar = QListWidget()
        sidebar.setFixedWidth(240)

        PAGE_DEFS = [
            ("dashboard", "لوحة التحكم", "dashboard.view"),
            ("receipts", "الإيصالات", "receipts.read"),
            ("orgs", "الجهات والمؤسسات", "organizations.read"),
            ("auth", "المستخدمون والصلاحيات", "users.read"),
            ("reports", "التقارير", "reports.read"),
            ("settings", "الإعدادات", "settings.read"),
            ("audit", "سجل التدقيق", "audit.read"),
            ("backup", "النسخ الاحتياطي", "backup.create"),
        ]

        self.page_keys = []
        self.sidebar_page_indices = {}
        sidebar_idx = 0
        for key, label, perm in PAGE_DEFS:
            try:
                check_permission(user, perm)
                sidebar.addItem(label)
                self.page_keys.append(key)
                self.sidebar_page_indices[key] = sidebar_idx
                sidebar_idx += 1
            except Exception:
                pass

        self.pages = QStackedWidget()
        page_map = {
            "dashboard": DashboardPage(user, auth_service),
            "receipts": ReceiptsPage(user),
            "orgs": OrgPage(user),
            "auth": UsersPage(user),
            "reports": ReportsPage(user),
            "settings": SettingsPage(user),
            "audit": AuditPage(user),
            "backup": BackupPage(user),
        }
        for key in self.page_keys:
            self.pages.addWidget(page_map[key])

        sidebar.currentRowChanged.connect(self._on_page_change)
        if self.page_keys:
            sidebar.setCurrentRow(0)

        panel = QFrame()
        panel_layout = QVBoxLayout(panel)
        panel_layout.addWidget(self.pages)

        shell.addWidget(panel)
        shell.addWidget(sidebar)
        self.setCentralWidget(root)

        self._session_timer = QTimer()
        self._session_timer.timeout.connect(self._check_session)
        self._session_timer.start(SESSION_CHECK_INTERVAL)

    def _on_page_change(self, index):
        self.pages.setCurrentIndex(index)
        if self.auth:
            self.auth.touch_activity()

    def _check_session(self):
        if not self.auth:
            return
        try:
            self.auth.check_session()
        except SessionExpiredError:
            QMessageBox.warning(self, "انتهت الجلسة", "انتهت صلاحية الجلسة بسبب عدم النشاط")
            self.close()


APP_STYLESHEET = f"""
QMainWindow, QWidget {{ background-color: {THEME['bg']}; color: {THEME['text']}; font-size: 13pt; }}
QPushButton {{ background-color: {THEME['primary']}; color: white; border: none; padding: 8px; min-height: 34px; }}
QPushButton:hover {{ background-color: #1a3d6e; }}
QLineEdit {{ background: {THEME['panel']}; border: 1px solid #CBD5E1; min-height: 34px; padding: 4px; }}
QListWidget {{ background: {THEME['panel']}; border: 1px solid #D1D5DB; }}
QTableWidget {{ background: {THEME['panel']}; border: 1px solid #D1D5DB; }}
QHeaderView::section {{ background-color: {THEME['panel']}; padding: 8px; border: 1px solid #D1D5DB; }}
"""


def run() -> None:
    self_repair()
    diag = run_all_checks()
    if not diag["all_ok"]:
        print(diagnose_and_report())

    init_db()
    seed_default_users()
    seed_organizations()
    seed_defaults()

    app = QApplication([])
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyleSheet(APP_STYLESHEET)

    auth_service = AuthService()
    login = LoginWindow(auth_service=auth_service)
    if login.exec() != QDialog.Accepted or not login.user:
        return

    if auth_service.needs_password_change():
        change = ChangePasswordDialog(auth_service)
        if change.exec() != QDialog.Accepted:
            QMessageBox.warning(None, "تحذير", "يجب تغيير كلمة المرور الافتراضية قبل متابعة استخدام النظام")
            return

    win = MainWindow(login.user, auth_service=auth_service)
    win.show()
    app.exec()
