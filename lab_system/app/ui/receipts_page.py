from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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
from lab_system.app.services.catalog_service import list_transaction_types
from lab_system.app.services.receipt_service import (
    delete_receipt,
    list_receipts,
    set_receipt_status,
)
from lab_system.app.ui.receipt_detail_dialog import ReceiptDetailDialog
from lab_system.app.ui.receipt_dialog import ReceiptDialog

PAGE_SIZE = 50

STATUS_STYLES = {
    "Draft": ("#6B7280", "مسودة"),
    "Approved": ("#059669", "معتمد"),
    "Rejected": ("#DC2626", "مرفوض"),
    "Archived": ("#D97706", "مؤرشف"),
    "Cancelled": ("#6B7280", "ملغي"),
}


class ReceiptsPage(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.current_page = 1
        self.total_count = 0
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._load()

    def _build_ui(self):
        title = QLabel("إدارة الإيصالات")
        title.setStyleSheet("font-size:16px;font-weight:700;margin-bottom:10px;")
        self.layout().addWidget(title)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث برقم الإيصال أو اسم الجهة...")
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        self.filter_status = QComboBox()
        self.filter_status.addItem("جميع الحالات", "")
        for key, (_, label) in STATUS_STYLES.items():
            self.filter_status.addItem(label, key)
        self.filter_status.currentIndexChanged.connect(self._on_filter)
        toolbar.addWidget(self.filter_status)

        self.filter_type = QComboBox()
        self.filter_type.addItem("جميع الأنواع", "")
        for t in list_transaction_types():
            self.filter_type.addItem(t["name"], t["id"])
        self.filter_type.currentIndexChanged.connect(self._on_filter)
        toolbar.addWidget(self.filter_type)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.dateChanged.connect(self._on_filter)
        toolbar.addWidget(QLabel("من:"))
        toolbar.addWidget(self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.dateChanged.connect(self._on_filter)
        toolbar.addWidget(QLabel("إلى:"))
        toolbar.addWidget(self.date_to)

        new_btn = QPushButton("إيصال جديد")
        new_btn.clicked.connect(self._new_receipt)
        toolbar.addWidget(new_btn)

        self.layout().addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "رقم الإيصال",
                "النوع",
                "الجهة المرسلة",
                "الجهة المستقبلة",
                "التاريخ",
                "الحالة",
                "المرسل",
                "إجراءات",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.layout().addWidget(self.table)

        pagination = QHBoxLayout()
        self.prev_btn = QPushButton("السابق")
        self.prev_btn.clicked.connect(self._prev_page)
        pagination.addWidget(self.prev_btn)

        self.page_label = QLabel("الصفحة 1")
        pagination.addWidget(self.page_label)

        self.next_btn = QPushButton("التالي")
        self.next_btn.clicked.connect(self._next_page)
        pagination.addWidget(self.next_btn)

        self.layout().addLayout(pagination)

    def _search_text(self):
        return self.search_input.text().strip()

    def _selected_status(self):
        return self.filter_status.currentData()

    def _selected_type(self):
        return self.filter_type.currentData()

    def _on_search(self):
        self.current_page = 1
        self._load()

    def _on_filter(self):
        self.current_page = 1
        self._load()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load()

    def _next_page(self):
        if self.current_page * PAGE_SIZE < self.total_count:
            self.current_page += 1
            self._load()

    def _load(self):
        rows, self.total_count = list_receipts(
            q=self._search_text(),
            status=self._selected_status(),
            tx_type_id=self._selected_type(),
            date_from=self.date_from.date().toString("yyyy-MM-dd"),
            date_to=self.date_to.date().toString("yyyy-MM-dd"),
            page=self.current_page,
            page_size=PAGE_SIZE,
        )
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["receipt_no"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["tx_type"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["sender_org"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(r["receiver_org"] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(r["created_at"] or ""))
            status_code = r["status"]
            _, status_ar = STATUS_STYLES.get(status_code, ("", status_code))
            item = QTableWidgetItem(status_ar)
            color, _ = STATUS_STYLES.get(status_code, ("#000", ""))
            item.setForeground(Qt.GlobalColor(color) if color.startswith("#") else None)
            self.table.setItem(i, 5, item)
            self.table.setItem(i, 6, QTableWidgetItem(r.get("sender_name", "")))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            view_btn = QPushButton("عرض")
            view_btn.setStyleSheet("font-size:10pt;padding:4px;")
            view_btn.clicked.connect(
                lambda checked, rid=r["id"]: self._view_receipt(rid)
            )
            actions_layout.addWidget(view_btn)

            edit_btn = QPushButton("تعديل")
            edit_btn.setStyleSheet("font-size:10pt;padding:4px;")
            edit_btn.clicked.connect(
                lambda checked, rid=r["id"]: self._edit_receipt(rid)
            )
            actions_layout.addWidget(edit_btn)

            if r["status"] == "Draft":
                approve_btn = QPushButton("اعتماد")
                approve_btn.setStyleSheet("font-size:10pt;padding:4px;")
                approve_btn.clicked.connect(
                    lambda checked, rid=r["id"]: self._change_status(
                        rid, "Approved"
                    )
                )
                actions_layout.addWidget(approve_btn)

            if r["status"] not in ("Archived", "Cancelled"):
                archive_btn = QPushButton("أرشفة")
                archive_btn.setStyleSheet("font-size:10pt;padding:4px;")
                archive_btn.clicked.connect(
                    lambda checked, rid=r["id"]: self._change_status(
                        rid, "Archived"
                    )
                )
                actions_layout.addWidget(archive_btn)

                cancel_btn = QPushButton("إلغاء")
                cancel_btn.setStyleSheet(
                    "font-size:10pt;padding:4px;color:#DC2626;"
                )
                cancel_btn.clicked.connect(
                    lambda checked, rid=r["id"]: self._change_status(
                        rid, "Cancelled"
                    )
                )
                actions_layout.addWidget(cancel_btn)

            if r["status"] == "Archived":
                del_btn = QPushButton("حذف")
                del_btn.setStyleSheet(
                    "font-size:10pt;padding:4px;color:#DC2626;"
                )
                del_btn.clicked.connect(
                    lambda checked, rid=r["id"]: self._delete_receipt(rid)
                )
                actions_layout.addWidget(del_btn)

            self.table.setCellWidget(i, 7, actions_widget)

        total_pages = max(
            1, (self.total_count + PAGE_SIZE - 1) // PAGE_SIZE
        )
        self.page_label.setText(
            f"الصفحة {self.current_page} من {total_pages} ({self.total_count})"
        )
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page * PAGE_SIZE < self.total_count)

    def _new_receipt(self):
        dlg = ReceiptDialog(self.current_user)
        if dlg.exec():
            log_action(
                self.current_user["id"],
                "receipt_created",
                f"إنشاء إيصال جديد",
            )
            self._load()

    def _view_receipt(self, receipt_id):
        dlg = ReceiptDetailDialog(self.current_user, receipt_id)
        dlg.exec()

    def _edit_receipt(self, receipt_id):
        dlg = ReceiptDialog(self.current_user, receipt_id=receipt_id)
        if dlg.exec():
            log_action(
                self.current_user["id"],
                "receipt_updated",
                f"تحديث الإيصال: {receipt_id}",
            )
            self._load()

    def _change_status(self, receipt_id, new_status):
        status_ar = STATUS_STYLES.get(new_status, ("", new_status))[1]
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد تغيير حالة الإيصال إلى {status_ar}؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            set_receipt_status(receipt_id, new_status)
            log_action(
                self.current_user["id"],
                f"receipt_{new_status.lower()}",
                f"تغيير حالة الإيصال {receipt_id} إلى {new_status}",
            )
            self._load()

    def _delete_receipt(self, receipt_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الإيصال permanently؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_receipt(receipt_id)
            log_action(
                self.current_user["id"],
                "receipt_deleted",
                f"حذف الإيصال: {receipt_id}",
            )
            self._load()
