from PySide6.QtGui import QColor
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

from lab_system.app.auth.permissions import check_permission
from lab_system.app.audit.logger import log_action
from lab_system.app.services.org_service import list_organizations, upsert_organization
from lab_system.app.ui.page_header import PageHeader
from lab_system.app.utils.constants import TABLE_STYLE

ORG_TYPES = [
    "مختبر صحة عامة",
    "مستشفى",
    "مركز رعاية صحية أولية",
    "بنك دم",
    "مركز أبحاث",
    "صيدلية",
    "أخرى",
]

ORG_TYPE_MAP = {
    "مختبر صحة عامة": "Public Health Laboratory",
    "مستشفى": "Hospital",
    "مركز رعاية صحية أولية": "Primary Health Care Center",
    "بنك دم": "Blood Bank",
    "مركز أبحاث": "Research Center",
    "صيدلية": "Pharmacy",
    "أخرى": "Other",
}

STATUS_MAP = {
    "Active": "نشط",
    "Inactive": "غير نشط",
    "Archived": "مؤرشف",
}

GOVERNORATES = [
    "بغداد",
    "البصرة",
    "نينوى",
    "أربيل",
    "السليمانية",
    "كركوك",
    "دهوك",
    "النجف",
    "كربلاء",
    "بابل",
    "ديالى",
    "الأنبار",
    "واسط",
    "ميسان",
    "ذي قار",
    "المثنى",
    "القادسية",
    "حلبجة",
]

GOV_MAP = {
    "بغداد": "Baghdad",
    "البصرة": "Basra",
    "نينوى": "Nineveh",
    "أربيل": "Erbil",
    "السليمانية": "Sulaymaniyah",
    "كركوك": "Kirkuk",
    "دهوك": "Duhok",
    "النجف": "Najaf",
    "كربلاء": "Karbala",
    "بابل": "Babil",
    "ديالى": "Diyala",
    "الأنبار": "Anbar",
    "واسط": "Wasit",
    "ميسان": "Maysan",
    "ذي قار": "Dhi Qar",
    "المثنى": "Muthanna",
    "القادسية": "Qadisiyyah",
    "حلبجة": "Halabja",
}


class OrgDialog(QDialog):
    def __init__(self, parent=None, org_data=None, current_user=None):
        super().__init__(parent)
        self.org_data = org_data
        self.current_user = current_user
        self.editing = org_data is not None
        self.setWindowTitle("تعديل جهة" if self.editing else "إضافة جهة جديدة")
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_form()
        if self.editing:
            self._populate()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _build_form(self):
        form = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم الجهة")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("رمز الجهة (مثل مخ-001)")
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
        self.status_combo.addItems(["نشط", "غير نشط", "مؤرشف"])

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
        eng_type = d.get("org_type", "")
        ar_type = next((k for k, v in ORG_TYPE_MAP.items() if v == eng_type), "")
        idx = self.type_combo.findText(ar_type or eng_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        eng_gov = d.get("governorate", "")
        ar_gov = next((k for k, v in GOV_MAP.items() if v == eng_gov), "")
        idx = self.gov_combo.findText(ar_gov or eng_gov)
        if idx >= 0:
            self.gov_combo.setCurrentIndex(idx)
        self.address_input.setText(d.get("address", ""))
        self.phone_input.setText(d.get("phone", ""))
        self.email_input.setText(d.get("email", ""))
        self.notes_input.setText(d.get("notes", ""))
        eng_status = d.get("status", "Active")
        ar_status = STATUS_MAP.get(eng_status, eng_status)
        idx = self.status_combo.findText(ar_status)
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
            "org_type": ORG_TYPE_MAP.get(self.type_combo.currentText(), self.type_combo.currentText()),
            "governorate": GOV_MAP.get(self.gov_combo.currentText(), self.gov_combo.currentText()),
            "address": self.address_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "notes": self.notes_input.text().strip(),
            "status": next((k for k, v in STATUS_MAP.items() if v == self.status_combo.currentText()), self.status_combo.currentText()),
            "logo_path": "",
        }
        try:
            upsert_organization(payload, user=self.current_user)
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
        header = PageHeader("إدارة الجهات والمؤسسات", "إضافة وتعديل وإدارة المؤسسات والجهات")
        self.layout().addWidget(header)

        self.search_input = header.add_search("بحث باسم الجهة أو الرمز...")
        self.search_input.textChanged.connect(self._load)

        header.add_action("إضافة جهة", self._add)

        from lab_system.app.ui.org_page import ORG_TYPES, STATUS_MAP
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.filter_type = QComboBox()
        self.filter_type.addItem("جميع الأنواع", "")
        for t in ORG_TYPES:
            self.filter_type.addItem(t, t)
        self.filter_type.currentIndexChanged.connect(self._load)
        filter_row.addWidget(QLabel("النوع:"))
        filter_row.addWidget(self.filter_type)

        self.filter_status_org = QComboBox()
        self.filter_status_org.addItem("جميع الحالات", "")
        for ar, eng in STATUS_MAP.items():
            self.filter_status_org.addItem(ar, eng)
        self.filter_status_org.currentIndexChanged.connect(self._load)
        filter_row.addWidget(QLabel("الحالة:"))
        filter_row.addWidget(self.filter_status_org)

        self.layout().addLayout(filter_row)

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
            ],
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.layout().addWidget(self.table)

    def _filter_text(self):
        return self.search_input.text().strip()

    def _load(self):
        q = self._filter_text()
        all_orgs = list_organizations()
        type_filter = self.filter_type.currentData()
        status_filter = self.filter_status_org.currentData()
        if type_filter:
            eng_type = ORG_TYPE_MAP.get(type_filter, type_filter)
            all_orgs = [o for o in all_orgs if o.get("org_type") == eng_type]
        if status_filter:
            all_orgs = [o for o in all_orgs if o.get("status") == status_filter]
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
            eng_type = od.get("org_type", "")
            ar_type = next((k for k, v in ORG_TYPE_MAP.items() if v == eng_type), eng_type)
            eng_gov = od.get("governorate", "")
            ar_gov = next((k for k, v in GOV_MAP.items() if v == eng_gov), eng_gov)
            eng_status = od.get("status", "")
            ar_status = STATUS_MAP.get(eng_status, eng_status)
            self.table.setItem(i, 0, QTableWidgetItem(od["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(od["code"]))
            self.table.setItem(i, 2, QTableWidgetItem(ar_type))
            self.table.setItem(i, 3, QTableWidgetItem(ar_gov))
            self.table.setItem(i, 4, QTableWidgetItem(od.get("phone", "")))
            self.table.setItem(i, 5, QTableWidgetItem(od.get("email", "")))
            status_item = QTableWidgetItem(ar_status)
            status_color = QColor("#059669" if eng_status == "Active" else "#6B7280")
            status_item.setForeground(status_color)
            status_item.setBackground(QColor(status_color.red(), status_color.green(), status_color.blue(), 30))
            self.table.setItem(i, 6, status_item)
            self.table.setItem(i, 7, QTableWidgetItem(od.get("notes", "")))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            edit_btn = QPushButton("تعديل")
            edit_btn.setStyleSheet("font-size:10pt;padding:4px;")
            edit_btn.clicked.connect(
                lambda _checked, od=dict(o): self._edit(od),
            )
            actions_layout.addWidget(edit_btn)

            toggle_label = "تعطيل" if o["status"] == "Active" else "تفعيل"
            toggle_btn = QPushButton(toggle_label)
            toggle_btn.setStyleSheet("font-size:10pt;padding:4px;")
            toggle_btn.clicked.connect(
                lambda _checked, oid=o["id"], s=o["status"]: self._toggle_status(
                    oid, s,
                ),
            )
            actions_layout.addWidget(toggle_btn)

            self.table.setCellWidget(i, 8, actions_widget)

    def _add(self):
        check_permission(self.current_user, 'organizations.create')
        dlg = OrgDialog(current_user=self.current_user)
        if dlg.exec():
            log_action(
                self.current_user["id"],
                "org_created",
                "إضافة جهة جديدة",
            )
            self._load()

    def _edit(self, org_data):
        check_permission(self.current_user, 'organizations.update')
        dlg = OrgDialog(org_data=org_data, current_user=self.current_user)
        if dlg.exec():
            log_action(
                self.current_user["id"],
                "org_updated",
                f"تحديث جهة: {org_data['name']}",
            )
            self._load()

    def _toggle_status(self, org_id, current_status):
        new_status = "Inactive" if current_status == "Active" else "Active"
        check_permission(self.current_user, 'organizations.update')
        upsert_organization({"id": org_id, "status": new_status}, user=self.current_user)
        log_action(
            self.current_user["id"],
            "org_status_toggled",
            f"تغيير حالة الجهة {org_id} إلى {new_status}",
        )
        self._load()
