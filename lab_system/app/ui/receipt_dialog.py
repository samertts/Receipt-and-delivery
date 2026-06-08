from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.services.catalog_service import (
    list_sample_types,
    list_transaction_types,
)
from lab_system.app.services.org_service import list_organizations
from lab_system.app.services.receipt_service import (
    create_receipt,
    get_receipt,
    update_receipt,
)
from lab_system.app.utils.constants import THEME

RECEIPT_STATUSES = ["مسودة", "معتمد", "مرفوض", "مؤرشف", "ملغي"]

STATUS_MAP = {
    "مسودة": "Draft",
    "معتمد": "Approved",
    "مرفوض": "Rejected",
    "مؤرشف": "Archived",
    "ملغي": "Cancelled",
}


class ReceiptDialog(QDialog):
    def __init__(self, current_user, receipt_id=None):
        super().__init__()
        self.current_user = current_user
        self.receipt_id = receipt_id
        self.editing = receipt_id is not None
        self.setWindowTitle("تعديل الاستلام" if self.editing else "استلام جديد")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.setLayoutDirection(Qt.RightToLeft)

        self._build_form()
        self._load_catalogs()
        if self.editing:
            self._load_receipt()

    def _build_form(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {THEME['border']};
                border-radius: 8px;
                background: {THEME['panel']};
                padding: 16px;
            }}
            QTabBar::tab {{
                padding: 10px 24px;
                font-size: 12pt;
                font-weight: 600;
                border: none;
                border-bottom: 3px solid transparent;
                color: #64748B;
            }}
            QTabBar::tab:selected {{
                color: {THEME['primary']};
                border-bottom: 3px solid {THEME['primary']};
            }}
            QTabBar::tab:hover {{
                color: {THEME['primary']};
            }}
        """)
        main.addWidget(self.tabs)

        self.tabs.addTab(self._build_info_tab(), "المعلومات الأساسية")
        self.tabs.addTab(self._build_samples_tab(), "العينات")
        self.tabs.addTab(self._build_review_tab(), "المراجعة النهائية")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        save_btn = QPushButton("حفظ")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['primary']}; color: white;
                border: none; border-radius: 6px;
                padding: 10px 32px; min-height: 40px;
                font-size: 13pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #0B3D6B; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['panel']}; color: #334155;
                border: 1px solid {THEME['border']}; border-radius: 6px;
                padding: 10px 32px; min-height: 40px; font-size: 13pt;
            }}
            QPushButton:hover {{ background-color: #F1F5F9; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        main.addLayout(btn_row)

    def _build_info_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(12)
        form.setContentsMargins(8, 8, 8, 8)

        self.tx_type = QComboBox()
        self.sender_org = QComboBox()
        self.receiver_org = QComboBox()
        self.sender_name = QLineEdit()
        self.sender_name.setPlaceholderText("اسم المرسل *")
        self.receiver_name = QLineEdit()
        self.receiver_name.setPlaceholderText("اسم المستلم *")
        self.sender_job = QLineEdit()
        self.sender_job.setPlaceholderText("مسمى وظيفة المرسل")
        self.receiver_job = QLineEdit()
        self.receiver_job.setPlaceholderText("مسمى وظيفة المستلم")
        self.auth_doc = QLineEdit()
        self.auth_doc.setPlaceholderText("رقم الوثيقة")
        self.auth_date = QDateEdit()
        self.auth_date.setCalendarPopup(True)
        self.auth_date.setDate(self.auth_date.date().currentDate())
        self.auth_date.setDisplayFormat("yyyy-MM-dd")

        self.status_combo = QComboBox()
        self.status_combo.addItems(RECEIPT_STATUSES)

        form.addRow("نوع المعاملة *:", self.tx_type)
        form.addRow("الجهة المرسلة:", self.sender_org)
        form.addRow("الجهة المستقبلة:", self.receiver_org)
        form.addRow("اسم المرسل *:", self.sender_name)
        form.addRow("اسم المستلم *:", self.receiver_name)
        form.addRow("مسمى وظيفة المرسل:", self.sender_job)
        form.addRow("مسمى وظيفة المستلم:", self.receiver_job)
        form.addRow("رقم الوثيقة:", self.auth_doc)
        form.addRow("تاريخ الوثيقة:", self.auth_date)
        form.addRow("الحالة:", self.status_combo)
        return tab

    def _build_samples_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(9)
        self.items_table.setHorizontalHeaderLabels(
            [
                "نوع العينة",
                "المجموع",
                "صالح",
                "تالف",
                "مرفوض",
                "غير مطابق",
                "حالة النقل",
                "ملاحظات",
                "حذف",
            ],
        )
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSortingEnabled(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.items_table)

        add_btn = QPushButton("+ إضافة عينة")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['panel']}; color: {THEME['primary']};
                border: 2px dashed {THEME['primary']}; border-radius: 8px;
                padding: 12px; font-size: 12pt; font-weight: 600;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background: #EFF6FF; border-color: #0B3D6B;
            }}
        """)
        add_btn.clicked.connect(self._add_item_row)
        layout.addWidget(add_btn)
        return tab

    def _build_review_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(12)
        form.setContentsMargins(8, 8, 8, 8)

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("ملاحظات عامة")
        self.transport_info = QLineEdit()
        self.transport_info.setPlaceholderText("معلومات النقل")
        self.additional_comments = QLineEdit()
        self.additional_comments.setPlaceholderText("تعليقات إضافية")

        form.addRow("ملاحظات:", self.notes)
        form.addRow("معلومات النقل:", self.transport_info)
        form.addRow("تعليقات إضافية:", self.additional_comments)
        return tab

    def _load_catalogs(self):
        for t in list_transaction_types():
            self.tx_type.addItem(t["name"], t["id"])
        for o in list_organizations(active_only=True):
            self.sender_org.addItem(o["name"], o["id"])
            self.receiver_org.addItem(o["name"], o["id"])

    def _load_receipt(self):
        receipt, items, _ = get_receipt(self.receipt_id)
        if not receipt:
            return
        idx = self.tx_type.findData(receipt["tx_type_id"])
        if idx >= 0:
            self.tx_type.setCurrentIndex(idx)
        idx = self.sender_org.findData(receipt["sender_org_id"])
        if idx >= 0:
            self.sender_org.setCurrentIndex(idx)
        idx = self.receiver_org.findData(receipt["receiver_org_id"])
        if idx >= 0:
            self.receiver_org.setCurrentIndex(idx)
        self.sender_name.setText(receipt["sender_name"])
        self.receiver_name.setText(receipt["receiver_name"])
        self.sender_job.setText(receipt["sender_job_title"] or "")
        self.receiver_job.setText(receipt["receiver_job_title"] or "")
        self.auth_doc.setText(receipt["auth_doc_no"] or "")
        if receipt["auth_date"]:
            from datetime import datetime

            self.auth_date.setDate(
                datetime.strptime(receipt["auth_date"], "%Y-%m-%d").date(),
            )
        eng_status = receipt["status"]
        ar_status = next((k for k, v in STATUS_MAP.items() if v == eng_status), eng_status)
        idx = self.status_combo.findText(ar_status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.notes.setText(receipt["notes"] or "")
        self.transport_info.setText(receipt["transport_info"] or "")
        self.additional_comments.setText(receipt["additional_comments"] or "")
        for i in items:
            self._add_item_row(i)

    def _add_item_row(self, data=None):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        sample_combo = QComboBox()
        for st in list_sample_types():
            sample_combo.addItem(st["name"], st["id"])
        if data and data.get("sample_type_id"):
            idx = sample_combo.findData(data["sample_type_id"])
            if idx >= 0:
                sample_combo.setCurrentIndex(idx)
        self.items_table.setCellWidget(row, 0, sample_combo)

        total_spin = QSpinBox()
        total_spin.setRange(0, 999999)
        valid_spin = QSpinBox()
        valid_spin.setRange(0, 999999)
        damaged_spin = QSpinBox()
        damaged_spin.setRange(0, 999999)
        rejected_spin = QSpinBox()
        rejected_spin.setRange(0, 999999)
        non_conf_spin = QSpinBox()
        non_conf_spin.setRange(0, 999999)

        if data:
            total_spin.setValue(int(data.get("total_count", 0)))
            valid_spin.setValue(int(data.get("valid_count", 0)))
            damaged_spin.setValue(int(data.get("damaged_count", 0)))
            rejected_spin.setValue(int(data.get("rejected_count", 0)))
            non_conf_spin.setValue(int(data.get("non_conforming_count", 0)))

        self.items_table.setCellWidget(row, 1, total_spin)
        self.items_table.setCellWidget(row, 2, valid_spin)
        self.items_table.setCellWidget(row, 3, damaged_spin)
        self.items_table.setCellWidget(row, 4, rejected_spin)
        self.items_table.setCellWidget(row, 5, non_conf_spin)

        transport_inp = QLineEdit()
        if data:
            transport_inp.setText(data.get("transport_condition", ""))
        self.items_table.setCellWidget(row, 6, transport_inp)

        notes_inp = QLineEdit()
        if data:
            notes_inp.setText(data.get("notes", ""))
        self.items_table.setCellWidget(row, 7, notes_inp)

        del_btn = QPushButton("حذف")
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 8, del_btn)

    def _remove_item_row(self, row):
        self.items_table.removeRow(row)

    def _collect_item_data(self):
        items = []
        for row in range(self.items_table.rowCount()):
            sample_widget = self.items_table.cellWidget(row, 0)
            if not sample_widget:
                continue
            items.append(
                {
                    "sample_type_id": sample_widget.currentData(),
                    "total_count": self.items_table.cellWidget(row, 1).value(),
                    "valid_count": self.items_table.cellWidget(row, 2).value(),
                    "damaged_count": self.items_table.cellWidget(row, 3).value(),
                    "rejected_count": self.items_table.cellWidget(row, 4).value(),
                    "non_conforming_count": self.items_table.cellWidget(
                        row, 5,
                    ).value(),
                    "transport_condition": self.items_table.cellWidget(
                        row, 6,
                    ).text(),
                    "notes": self.items_table.cellWidget(row, 7).text(),
                },
            )
        return items

    def _save(self):
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "خطأ", "يجب إضافة عينة واحدة على الأقل")
            self.tabs.setCurrentIndex(1)
            return
        if not self.sender_name.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المرسل")
            self.tabs.setCurrentIndex(0)
            return
        if not self.receiver_name.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المستلم")
            self.tabs.setCurrentIndex(0)
            return

        data = {
            "tx_type_id": self.tx_type.currentData(),
            "sender_org_id": self.sender_org.currentData(),
            "receiver_org_id": self.receiver_org.currentData(),
            "sender_name": self.sender_name.text().strip(),
            "receiver_name": self.receiver_name.text().strip(),
            "sender_job_title": self.sender_job.text().strip(),
            "receiver_job_title": self.receiver_job.text().strip(),
            "auth_doc_no": self.auth_doc.text().strip(),
            "auth_date": self.auth_date.date().toString("yyyy-MM-dd"),
            "notes": self.notes.text().strip(),
            "transport_info": self.transport_info.text().strip(),
            "additional_comments": self.additional_comments.text().strip(),
            "status": STATUS_MAP.get(self.status_combo.currentText(), self.status_combo.currentText()),
        }
        items = self._collect_item_data()

        try:
            for i in items:
                total = i["total_count"]
                valid = i["valid_count"]
                damaged = i["damaged_count"]
                rejected = i["rejected_count"]
                non_conf = i["non_conforming_count"]
                if total != valid + damaged + rejected + non_conf:
                    raise ValueError(
                        "المجموع يجب أن يساوي مجموع الصالح + التالف + المرفوض + غير المطابق",
                    )
            if self.editing:
                update_receipt(self.receipt_id, data, items)
            else:
                self._rid, self._no = create_receipt(data, items, self.current_user["id"])
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "خطأ في البيانات", str(e))
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل الحفظ: {e}")
