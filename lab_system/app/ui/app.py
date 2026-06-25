from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.audit.logger import log_action
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
from lab_system.app.ui.dashboard_page import DashboardPage
from lab_system.app.ui.notifications import toast
from lab_system.app.ui.org_page import OrgPage
from lab_system.app.ui.receipts_page import ReceiptsPage
from lab_system.app.ui.reports_page import ReportsPage
from lab_system.app.ui.settings_page import SettingsPage
from lab_system.app.ui.sidebar import ModernSidebar
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _save(self):
        if self.new_password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "خطأ", "كلمتا المرور غير متطابقتين")
            return
        pwd_error = _validate_password(self.new_password.text())
        if pwd_error:
            QMessageBox.warning(self, "خطأ", pwd_error)
            return
        try:
            self.auth.change_password(
                self.old_password.text(), self.new_password.text()
            )
            toast(self, "تم تغيير كلمة المرور بنجاح", "success")
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
        submit.setDefault(True)
        submit.setToolTip("دخول (Enter)")
        submit.clicked.connect(self._login)
        self.password.returnPressed.connect(self._login)
        self.username.returnPressed.connect(lambda: self.password.setFocus())

        layout.addWidget(title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(submit)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._login()
        else:
            super().keyPressEvent(event)

    def _login(self) -> None:
        try:
            self.user = self.auth.login(
                self.username.text().strip(),
                self.password.text(),
            )
            log_action(self.user["id"], "login_success", "desktop_login")
            self.accept()
        except AuthenticationError as exc:
            QMessageBox.warning(self, "خطأ", str(exc))
        except Exception as exc:
            log_action("unknown", "login_error", str(exc))
            QMessageBox.warning(self, "خطأ", f"حدث خطأ غير متوقع: {exc}")


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("حول النظام")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFixedSize(500, 450)
        layout = QVBoxLayout(self)

        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size:20px;font-weight:700;color:#2563EB;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        tabs = QTabWidget()
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        try:
            from lab_system.app.settings.config import CONFIG
            ver = CONFIG.app_version
        except Exception:
            ver = "unknown"
        try:
            from lab_system.app import build_metadata
            build_info = build_metadata.get_build_info()
        except Exception:
            build_info = {}

        for text in [
            f"الإصدار: {ver}",
            f"تاريخ البناء: {build_info.get('build_date', 'N/A')}",
            f"التفديع: {build_info.get('git_commit', 'N/A')[:12]}",
            f"الفرع: {build_info.get('git_branch', 'N/A')}",
            f"رقم البناء: {build_info.get('build_number', 'N/A')}",
            f"بايثون: {build_info.get('python_version', 'N/A')}",
            "",
            "نظام إدارة استلام وتسليم العينات المخبرية",
            "لجنة الصحة العراقية - دائرة المختبرات",
            "",
            "© 2026 جميع الحقوق محفوظة",
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size:12pt;")
            about_layout.addWidget(lbl)
        about_layout.addStretch()

        sys_tab = QWidget()
        sys_layout = QVBoxLayout(sys_tab)
        import platform
        import sys as _sys

        sys_info = [
            ("نظام التشغيل", platform.platform()),
            ("بايثون", _sys.version.split()[0]),
            ("المعالج", platform.machine()),
            ("المستخدم", platform.node()),
        ]
        if build_info:
            sys_info.extend([
                ("نوع البناء", build_info.get("build_type", "N/A")),
                ("معرف التفديع", build_info.get("git_commit", "N/A")[:12]),
            ])
        for label, value in sys_info:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("font-weight:600;")
            val = QLabel(value)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            sys_layout.addLayout(row)
        sys_layout.addStretch()

        tabs.addTab(about_tab, "حول")
        tabs.addTab(sys_tab, "معلومات النظام")
        layout.addWidget(tabs)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, user, auth_service=None) -> None:
        super().__init__()
        self.user = user
        self.auth = auth_service or AuthService()
        self.setWindowTitle(APP_NAME)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setMinimumSize(1024, 600)
        self.setLayoutDirection(Qt.RightToLeft)

        root = QWidget()
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = ModernSidebar(user)
        self.sidebar.page_changed.connect(self._on_page_change)

        page_map = {
            "dashboard": DashboardPage(
                user, auth_service=auth_service, navigate_cb=self._navigate_to
            ),
            "receipts": ReceiptsPage(user),
            "orgs": OrgPage(user),
            "samples": ReceiptsPage(user),
            "users": UsersPage(user),
            "reports": ReportsPage(user),
            "statistics": ReportsPage(user),
            "audit": AuditPage(user),
            "backup": BackupPage(user),
            "settings": SettingsPage(user),
        }

        self.pages = QStackedWidget()
        self.page_keys = self.sidebar.items
        for key in self.page_keys:
            if key in page_map:
                self.pages.addWidget(page_map[key])

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        panel = QFrame()
        panel.setObjectName("ContentPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.addWidget(self.pages)
        scroll_area.setWidget(panel)

        shell.addWidget(self.sidebar)
        shell.addWidget(scroll_area, 1)
        self.setCentralWidget(root)

        if self.page_keys:
            self.sidebar.set_active(self.page_keys[0])
            self.pages.setCurrentIndex(0)

        self._session_timer = QTimer()
        self._session_timer.timeout.connect(self._check_session)
        self._session_timer.start(SESSION_CHECK_INTERVAL)

        from lab_system.app.sync.service import sync_service

        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(sync_service.sync_pending)
        self._sync_timer.start(60000)

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        refresh_action = QAction("تحديث", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self._refresh_current)
        self.addAction(refresh_action)

        search_action = QAction("بحث", self)
        search_action.setShortcut(QKeySequence.Find)
        search_action.triggered.connect(self._focus_search)
        self.addAction(search_action)

        new_action = QAction("جديد", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_item)
        self.addAction(new_action)

        help_action = QAction("مساعدة", self)
        help_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_H))
        help_action.triggered.connect(self._show_about)
        self.addAction(help_action)

        dash_action = QAction("لوحة القيادة", self)
        dash_action.setShortcut(QKeySequence(Qt.ALT | Qt.Key_1))
        dash_action.triggered.connect(lambda: self._navigate_to("dashboard"))
        self.addAction(dash_action)

        receipts_action = QAction("الإيصالات", self)
        receipts_action.setShortcut(QKeySequence(Qt.ALT | Qt.Key_2))
        receipts_action.triggered.connect(lambda: self._navigate_to("receipts"))
        self.addAction(receipts_action)

        orgs_action = QAction("الجهات", self)
        orgs_action.setShortcut(QKeySequence(Qt.ALT | Qt.Key_3))
        orgs_action.triggered.connect(lambda: self._navigate_to("orgs"))
        self.addAction(orgs_action)

        users_action = QAction("المستخدمين", self)
        users_action.setShortcut(QKeySequence(Qt.ALT | Qt.Key_4))
        users_action.triggered.connect(lambda: self._navigate_to("users"))
        self.addAction(users_action)

    def _refresh_current(self):
        page = self.pages.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()
        elif hasattr(page, "_load"):
            page._load()

    def _focus_search(self):
        page = self.pages.currentWidget()
        for attr in ("search_input", "search"):
            inp = getattr(page, attr, None)
            if inp:
                inp.setFocus()
                break

    def _new_item(self):
        page = self.pages.currentWidget()
        if hasattr(page, "_new_receipt"):
            page._new_receipt()
        elif hasattr(page, "_add"):
            page._add()

    def _on_page_change(self, key):
        idx = self.page_keys.index(key) if key in self.page_keys else 0
        self.pages.setCurrentIndex(idx)
        if self.auth:
            self.auth.touch_activity()

    def _show_about(self):
        dlg = AboutDialog()
        dlg.exec()

    def _navigate_to(self, key):
        """Public navigation helper, used by quick action callbacks."""
        if key in self.page_keys:
            self._on_page_change(key)
            self.sidebar.set_active(key)

    def _check_session(self):
        if not self.auth:
            return
        try:
            self.auth.check_session()
        except SessionExpiredError:
            QMessageBox.warning(
                self, "انتهت الجلسة", "انتهت صلاحية الجلسة بسبب عدم النشاط"
            )
            self.close()


APP_STYLESHEET = f"""
QMainWindow, QWidget {{ background-color: {THEME["bg"]}; color: {THEME["text"]}; font-size: 13pt; font-family: 'Segoe UI', 'Tahoma', sans-serif; }}
QMainWindow::separator {{ background: {THEME["border"]}; width: 1px; }}

QPushButton {{ background-color: {THEME["primary"]}; color: white; border: none; border-radius: 6px; padding: 8px 20px; min-height: 38px; font-size: 12pt; font-weight: 600; }}
QPushButton:hover {{ background-color: #0B3D6B; }}
QPushButton:pressed {{ background-color: #092D4F; }}
QPushButton:focus {{ outline: 2px solid {THEME["primary"]}; outline-offset: 2px; }}
QPushButton:disabled {{ background-color: #CBD5E1; color: #94A3B8; }}

QLineEdit {{ background: {THEME["panel"]}; border: 1px solid #CBD5E1; border-radius: 6px; min-height: 38px; padding: 4px 12px; font-size: 12pt; }}
QLineEdit:focus {{ border: 2px solid {THEME["primary"]}; background: #FFFFFF; }}
QLineEdit:disabled {{ background: #F1F5F9; color: #94A3B8; }}

QComboBox {{ background: {THEME["panel"]}; border: 1px solid #CBD5E1; border-radius: 6px; min-height: 38px; padding: 4px 12px; font-size: 12pt; }}
QComboBox:focus {{ border: 2px solid {THEME["primary"]}; }}
QComboBox::drop-down {{ border: none; width: 30px; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #64748B; margin-right: 8px; }}

QTableWidget {{ background: {THEME["panel"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; gridline-color: #F1F5F9; font-size: 11pt; alternate-background-color: {THEME["table_alt"]}; }}
QTableWidget::item {{ padding: 10px 8px; border-bottom: 1px solid #F1F5F9; }}
QTableWidget::item:selected {{ background: #DBEAFE; color: #1E40AF; font-weight: 600; }}
QTableWidget::item:hover {{ background: #F1F5F9; }}
QTableWidget::item:selected:hover {{ background: #BFDBFE; }}
QHeaderView::section {{ background-color: {THEME["header_bg"]}; padding: 12px 8px; border: none; border-bottom: 2px solid {THEME["border"]}; font-size: 10pt; font-weight: bold; color: #475569; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: #F1F5F9; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #94A3B8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QDateEdit {{ background: {THEME["panel"]}; border: 1px solid #CBD5E1; border-radius: 6px; min-height: 38px; padding: 4px 12px; }}
QDateEdit:focus {{ border: 2px solid {THEME["primary"]}; }}

QSpinBox {{ background: {THEME["panel"]}; border: 1px solid #CBD5E1; border-radius: 6px; min-height: 38px; padding: 4px 12px; }}
QSpinBox:focus {{ border: 2px solid {THEME["primary"]}; }}

QGroupBox {{ font-weight: bold; border: 1px solid {THEME["border"]}; border-radius: 8px; margin-top: 12px; padding-top: 16px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}

#ContentPanel {{ background: {THEME["bg"]}; border: none; }}
#StatCard {{ background: {THEME["panel"]}; border: 1px solid {THEME["border"]}; border-radius: 12px; padding: 16px; }}
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
            QMessageBox.warning(
                None,
                "تحذير",
                "يجب تغيير كلمة المرور الافتراضية قبل متابعة استخدام النظام",
            )
            return

    win = MainWindow(login.user, auth_service=auth_service)
    win.show()
    app.exec()
