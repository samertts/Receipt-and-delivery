from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
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
from lab_system.app.database.db import init_db
from lab_system.app.diagnostics.startup import diagnose_and_report, run_all_checks, self_repair
from lab_system.app.services.auth_service import AuthService
from lab_system.app.services.seed_service import seed_organizations
from lab_system.app.services.user_service import seed_default_users
from lab_system.app.services.catalog_service import seed_defaults
from lab_system.app.ui.audit_page import AuditPage
from lab_system.app.ui.backup_page import BackupPage
from lab_system.app.ui.org_page import OrgPage
from lab_system.app.ui.receipts_page import ReceiptsPage
from lab_system.app.ui.reports_page import ReportsPage
from lab_system.app.ui.settings_page import SettingsPage
from lab_system.app.ui.users_page import UsersPage
from lab_system.app.utils.constants import APP_NAME, DEFAULT_WINDOW_SIZE, THEME
from lab_system.app.utils.errors import AuthenticationError


class LoginWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.user = None
        self.auth = AuthService()
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
                self.username.text().strip(), self.password.text()
            )
            log_action(self.user["id"], "login_success", "desktop_login")
            self.accept()
        except AuthenticationError as exc:
            QMessageBox.warning(self, "خطأ", str(exc))
        except Exception as exc:
            log_action("unknown", "login_error", str(exc))
            QMessageBox.warning(self, "خطأ", f"حدث خطأ غير متوقع: {exc}")


class DashboardPage(QWidget):
    def __init__(self, user) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        header = QLabel(f"مرحباً {user['full_name']}")
        header.setStyleSheet("font-size:18px;font-weight:700;")
        layout.addWidget(header)

        layout.addWidget(QLabel(f"الصلاحية: {user['role']}"))
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


class MainWindow(QMainWindow):
    def __init__(self, user) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle(APP_NAME)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setLayoutDirection(Qt.RightToLeft)

        root = QWidget()
        shell = QHBoxLayout(root)

        sidebar = QListWidget()
        sidebar.setFixedWidth(240)
        items = [
            ("dashboard", "لوحة التحكم"),
            ("receipts", "الإيصالات"),
            ("orgs", "الجهات والمؤسسات"),
            ("auth", "المستخدمون والصلاحيات"),
            ("reports", "التقارير"),
            ("settings", "الإعدادات"),
            ("audit", "سجل التدقيق"),
            ("backup", "النسخ الاحتياطي"),
        ]
        for _, label in items:
            sidebar.addItem(label)

        self.pages = QStackedWidget()
        self.pages.addWidget(DashboardPage(user))
        self.pages.addWidget(ReceiptsPage(user))
        self.pages.addWidget(OrgPage(user))
        self.pages.addWidget(UsersPage(user))
        self.pages.addWidget(ReportsPage(user))
        self.pages.addWidget(SettingsPage(user))
        self.pages.addWidget(AuditPage(user))
        self.pages.addWidget(BackupPage(user))

        sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        sidebar.setCurrentRow(0)

        panel = QFrame()
        panel_layout = QVBoxLayout(panel)
        panel_layout.addWidget(self.pages)

        shell.addWidget(panel)
        shell.addWidget(sidebar)
        self.setCentralWidget(root)


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
    repairs = self_repair()
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

    login = LoginWindow()
    if login.exec() != QDialog.Accepted or not login.user:
        return

    win = MainWindow(login.user)
    win.show()
    app.exec()
