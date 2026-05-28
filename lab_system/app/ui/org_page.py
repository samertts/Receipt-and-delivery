from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
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

from lab_system.app.audit.logger import log_action
from lab_system.app.database import db as _db
from lab_system.app.services.org_service import list_organizations, upsert_organization

ORG_TYPES = [
    "Public Health Laboratory",
    "Hospital",
    "Primary Health Care Center",
    "Blood Bank",
    "Research Center",
    "Pharmacy",
    "Other",
]
GOVERNORATES = [
    "Baghdad",
    "Basra",
    "Nineveh",
    "Erbil",
    "Sulaymaniyah",
    "Kirkuk",
    "Duhok",
    "Najaf",
    "Karbala",
    "Babil",
    "Diyala",
    "Anbar",
    "Wasit",
    "Maysan",
    "Dhi Qar",
    "Muthanna",
    "Qadisiyyah",
    "Halabja",
]


class OrgDialog(QDialog):
    def __init__(self, org_data=None):
        super().__init__()
        self.org_data = org_data
        self.editing = org_data is not None
        self.setWindowTitle("تعديل جهة" if self.editing else "إضافة جهة جديدة")
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_form()
        if self.editing:
            self._populate()

    def _build_form(self):
        form = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم الجهة")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("رمز الجهة (مثل IQH-001)")
        self.type_combo = QComboBox()
        self.type_combo.addItems(ORG_TYPES)
        self.gov_combo = QComboBox()
        self.gov_combo.addItems(GOVERNORATES)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("العنوان")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني")
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Archived"])

        form.addRow("الاسم:", self.name_input)
        form.addRow("الرمز:", self.code_input)
        form.addRow("النوع:", self.type_combo)
        form.addRow("المحافظة:", self.gov_combo)
        form.addRow("العنوان:", self.address_input)
        form.addRow("الهاتف:", self.phone_input)
        form.addRow("البريد الإلكتروني:", self.email_input)
        form.addRow("ملاحظات:", self.notes_input)
        form.addRow("الحالة:", self.status_combo)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        form.addRow(btn_row)

    def _populate(self):
        d = self.org_data
        self.name_input.setText(d.get("name", ""))
        self.code_input.setText(d.get("code", ""))
        idx = self.type_combo.findText(d.get("org_type", ""))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        idx = self.gov_combo.findText(d.get("governorate", ""))
        if idx >= 0:
            self.gov_combo.setCurrentIndex(idx)
        self.address_input.setText(d.get("address", ""))
        self.phone_input.setText(d.get("phone", ""))
        self.email_input.setText(d.get("email", ""))
        self.notes_input.setText(d.get("notes", ""))
        idx = self.status_combo.findText(d.get("status", "Active"))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

    def _save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الجهة")
            return
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال رمز الجهة")
            return
        payload = {
            "id": self.org_data["id"] if self.editing else None,
            "name": self.name_input.text().strip(),
            "code": self.code_input.text().strip(),
            "org_type": self.type_combo.currentText(),
            "governorate": self.gov_combo.currentText(),
            "address": self.address_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "notes": self.notes_input.text().strip(),
            "status": self.status_combo.currentText(),
            "logo_path": "",
        }
        try:
            upsert_organization(payload)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل الحفظ: {e}")


class OrgPage(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._load()

    def _build_ui(self):
        title = QLabel("إدارة الجهات والمؤسسات")
        title.setStyleSheet("font-size:16px;font-weight:700;margin-bottom:10px;")
        self.layout().addWidget(title)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث باسم الجهة أو الرمز...")
        self.search_input.textChanged.connect(self._load)
        toolbar.addWidget(self.search_input)

        add_btn = QPushButton("إضافة جهة")
        add_btn.clicked.connect(self._add)
        toolbar.addWidget(add_btn)

        self.layout().addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "الاسم",
                "الرمز",
                "النوع",
                "المحافظة",
                "الهاتف",
                "البريد",
                "الحالة",
                "ملاحظات",
                "إجراءات",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout().addWidget(self.table)

    def _filter_text(self):
        return self.search_input.text().strip()

    def _load(self):
        q = self._filter_text()
        all_orgs = list_organizations()
        if q:
            ql = q.lower()
            filtered = [
                o
                for o in all_orgs
                if ql in o["name"].lower() or ql in o["code"].lower()
            ]
        else:
            filtered = all_orgs

        self.table.setRowCount(len(filtered))
        for i, o in enumerate(filtered):
            od = dict(o)
            self.table.setItem(i, 0, QTableWidgetItem(od["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(od["code"]))
            self.table.setItem(i, 2, QTableWidgetItem(od.get("org_type", "")))
            self.table.setItem(i, 3, QTableWidgetItem(od.get("governorate", "")))
            self.table.setItem(i, 4, QTableWidgetItem(od.get("phone", "")))
            self.table.setItem(i, 5, QTableWidgetItem(od.get("email", "")))
            self.table.setItem(i, 6, QTableWidgetItem(od.get("status", "")))
            self.table.setItem(i, 7, QTableWidgetItem(od.get("notes", "")))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            edit_btn = QPushButton("تعديل")
            edit_btn.setStyleSheet("font-size:10pt;padding:4px;")
            edit_btn.clicked.connect(
                lambda checked, od=dict(o): self._edit(od)
            )
            actions_layout.addWidget(edit_btn)

            toggle_label = "تعطيل" if o["status"] == "Active" else "تفعيل"
            toggle_btn = QPushButton(toggle_label)
            toggle_btn.setStyleSheet("font-size:10pt;padding:4px;")
            toggle_btn.clicked.connect(
                lambda checked, oid=o["id"], s=o["status"]: self._toggle_status(
                    oid, s
                )
            )
            actions_layout.addWidget(toggle_btn)

            self.table.setCellWidget(i, 8, actions_widget)

    def _add(self):
        dlg = OrgDialog()
        if dlg.exec():
            log_action(
                self.current_user["id"],
                "org_created",
                "إضافة جهة جديدة",
            )
            self._load()

    def _edit(self, org_data):
        dlg = OrgDialog(org_data=org_data)
        if dlg.exec():
            log_action(
                self.current_user["id"],
                "org_updated",
                f"تحديث جهة: {org_data['name']}",
            )
            self._load()

    def _toggle_status(self, org_id, current_status):
        new_status = "Inactive" if current_status == "Active" else "Active"
        with _db.get_conn() as conn:
            conn.execute(
                "UPDATE organizations SET status=? WHERE id=?",
                (new_status, org_id),
            )
        log_action(
            self.current_user["id"],
            "org_status_toggled",
            f"تغيير حالة الجهة {org_id} إلى {new_status}",
        )
        self._load()
