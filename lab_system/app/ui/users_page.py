from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.auth.permissions import check_permission
from lab_system.app.audit.logger import log_action
from lab_system.app.services.org_service import list_organizations
from lab_system.app.services.user_service import (
    create_user,
    disable_user,
    list_users,
    reset_password,
)
from lab_system.app.utils.validators import validate_password, validate_username

ROLE_MAP = {
    "مدير": "Admin",
    "مشرف": "Supervisor",
    "مستخدم": "User",
    "مدقق": "Auditor",
}
ROLE_DISPLAY = {v: k for k, v in ROLE_MAP.items()}

STATUS_MAP = {
    "Active": "نشط",
    "Inactive": "غير نشط",
}


class UsersPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        header = PageHeader("إدارة المستخدمين والصلاحيات", "إضافة وتعديل وإدارة المستخدمين")
        self.layout().addWidget(header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.filter_role = QComboBox()
        self.filter_role.addItem("جميع الصلاحيات", "")
        for ar_role in ROLE_MAP:
            self.filter_role.addItem(ar_role, ROLE_MAP[ar_role])
        self.filter_role.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.filter_role)

        self.filter_status = QComboBox()
        self.filter_status.addItem("جميع الحالات", "")
        self.filter_status.addItem("نشط", "Active")
        self.filter_status.addItem("غير نشط", "Inactive")
        self.filter_status.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.filter_status)

        self.layout().addLayout(filter_row)

        self._build_user_form()
        self._build_user_table()
        self.refresh()

    def _build_user_form(self):
        form = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("الاسم الكامل")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["مدير", "مشرف", "مستخدم", "مدقق"])
        self.institution_combo = QComboBox()
        self.institution_combo.addItem("-- بدون --", "")
        for o in list_organizations(active_only=True):
            self.institution_combo.addItem(o["name"], o["id"])

        add_btn = QPushButton("إضافة مستخدم")
        add_btn.clicked.connect(self._add_user)

        form.addRow("اسم المستخدم:", self.username_input)
        form.addRow("الاسم الكامل:", self.fullname_input)
        form.addRow("كلمة المرور:", self.password_input)
        form.addRow("الصلاحية:", self.role_combo)
        form.addRow("الجهة:", self.institution_combo)
        form.addRow(add_btn)
        self.layout().addLayout(form)

    def _build_user_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["الاسم", "المستخدم", "الصلاحية", "الجهة", "الحالة", "إجراءات"],
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.layout().addWidget(self.table)

    def _add_user(self):
        check_permission(self.current_user, 'users.create')
        username = self.username_input.text().strip()
        full_name = self.fullname_input.text().strip()
        password = self.password_input.text()
        role = ROLE_MAP.get(self.role_combo.currentText(), self.role_combo.currentText())
        institution_id = self.institution_combo.currentData()

        error = validate_username(username)
        if error:
            QMessageBox.warning(self, "خطأ", error)
            return
        error = validate_password(password)
        if error:
            QMessageBox.warning(self, "خطأ", error)
            return

        try:
            create_user(full_name, username, password, role, institution_id)
            log_action(
                self.current_user["id"],
                "user_created",
                f"إنشاء مستخدم: {username}",
            )
            QMessageBox.information(self, "نجاح", f"تم إنشاء المستخدم {username}")
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def refresh(self):
        users = list_users()
        role_filter = self.filter_role.currentData()
        status_filter = self.filter_status.currentData()
        if role_filter:
            users = [u for u in users if u["role"] == role_filter]
        if status_filter:
            users = [u for u in users if u["status"] == status_filter]
        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            ud = dict(u)
            self.table.setItem(i, 0, QTableWidgetItem(ud["full_name"]))
            self.table.setItem(i, 1, QTableWidgetItem(ud["username"]))
            self.table.setItem(i, 2, QTableWidgetItem(ROLE_DISPLAY.get(ud["role"], ud["role"])))
            self.table.setItem(
                i, 3, QTableWidgetItem(ud.get("institution_name") or "-"),
            )
            self.table.setItem(i, 4, QTableWidgetItem(STATUS_MAP.get(ud["status"], ud["status"])))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            if u["status"] == "Active":
                disable_btn = QPushButton("تعطيل")
                disable_btn.setStyleSheet("font-size:10pt;padding:4px;")
                disable_btn.clicked.connect(
                    lambda _, uid=u["id"], uname=u["username"]: self._disable_user(
                        uid, uname,
                    ),
                )
                actions_layout.addWidget(disable_btn)
            else:
                enable_btn = QPushButton("تفعيل")
                enable_btn.setStyleSheet("font-size:10pt;padding:4px;")
                enable_btn.clicked.connect(
                    lambda _, uid=u["id"]: self._enable_user(uid),
                )
                actions_layout.addWidget(enable_btn)

            reset_btn = QPushButton("إعادة تعيين كلمة المرور")
            reset_btn.setStyleSheet("font-size:10pt;padding:4px;")
            reset_btn.clicked.connect(
                lambda _, uid=u["id"]: self._reset_password_dialog(uid),
            )
            actions_layout.addWidget(reset_btn)

            self.table.setCellWidget(i, 5, actions_widget)

    def _disable_user(self, user_id, username):
        check_permission(self.current_user, 'users.update')
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد تعطيل المستخدم {username}؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            disable_user(user_id)
            log_action(
                self.current_user["id"],
                "user_disabled",
                f"تعطيل مستخدم: {username}",
            )
            self.refresh()

    def _enable_user(self, user_id):
        check_permission(self.current_user, 'users.update')
        from lab_system.app.services.user_service import enable_user
        enable_user(user_id)
        log_action(
            self.current_user["id"],
            "user_enabled",
            f"تفعيل مستخدم: {user_id}",
        )
        self.refresh()

    def _reset_password_dialog(self, user_id):
        check_permission(self.current_user, 'users.reset_password')
        password, ok = QLineEdit.getText(
            self, "إعادة تعيين كلمة المرور", "كلمة المرور الجديدة:",
        )
        if ok and password:
            error = validate_password(password)
            if error:
                QMessageBox.warning(self, "خطأ", error)
                return
            reset_password(user_id, password)
            log_action(
                self.current_user["id"],
                "password_reset",
                f"إعادة تعيين كلمة المرور للمستخدم: {user_id}",
            )
            QMessageBox.information(self, "نجاح", "تم إعادة تعيين كلمة المرور")
