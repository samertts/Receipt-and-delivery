from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from lab_system.app.attachments.manager import save_attachment
from lab_system.app.audit.logger import log_action
from lab_system.app.printing.receipt_pdf import generate_receipt_pdf
from lab_system.app.services.receipt_service import get_receipt
from lab_system.app.ui.notifications import toast
from lab_system.app.utils.constants import THEME, TABLE_STYLE


def _open_file_safe(path):
    try:
        from sys import platform as _p

        if _p == "win32":
            import os

            os.startfile(str(path))
        else:
            import subprocess

            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


STATUS_TRANSLATION = {
    "Draft": "مسودة",
    "Approved": "معتمد",
    "Rejected": "مرفوض",
    "Archived": "مؤرشف",
    "Cancelled": "ملغي",
}

STATUS_STYLES = {
    "Draft": "color:#6B7280;font-weight:bold;",
    "Approved": "color:#059669;font-weight:bold;",
    "Rejected": "color:#DC2626;font-weight:bold;",
    "Archived": "color:#D97706;font-weight:bold;",
    "Cancelled": "color:#6B7280;font-weight:bold;",
}

_SECTION = f"""
    QLabel {{
        font-size: 10pt; font-weight: 700; color: {THEME["primary"]};
        padding: 2px 0; margin-top: 6px;
    }}
"""


class ReceiptDetailDialog(QDialog):
    def __init__(self, current_user, receipt_id):
        super().__init__()
        self.current_user = current_user
        self.receipt_id = receipt_id
        self.setWindowTitle("تفاصيل الإيصال")
        self.setMinimumWidth(800)
        self.setMinimumHeight(580)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._load()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    @staticmethod
    def _section_header(text):
        lbl = QLabel(text)
        lbl.setStyleSheet(_SECTION)
        return lbl

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(4)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size:15px;font-weight:700;")
        main.addWidget(self.title_label)

        self.status_label = QLabel()
        main.addWidget(self.status_label)

        main.addWidget(self._section_header("بيانات المعاملة"))
        f1 = QFormLayout()
        f1.setSpacing(4)
        f1.setContentsMargins(0, 0, 0, 0)
        self.tx_type_label = QLabel()
        self.sender_org_label = QLabel()
        self.receiver_org_label = QLabel()
        f1.addRow("نوع المعاملة:", self.tx_type_label)
        f1.addRow("الجهة المرسلة:", self.sender_org_label)
        f1.addRow("الجهة المستقبلة:", self.receiver_org_label)
        main.addLayout(f1)

        main.addWidget(self._section_header("جهات الاتصال"))
        f2 = QFormLayout()
        f2.setSpacing(4)
        f2.setContentsMargins(0, 0, 0, 0)
        self.sender_name_label = QLabel()
        self.receiver_name_label = QLabel()
        self.sender_job_label = QLabel()
        self.receiver_job_label = QLabel()
        f2.addRow("اسم المرسل:", self.sender_name_label)
        f2.addRow("اسم المستلم:", self.receiver_name_label)
        f2.addRow("مسمى وظيفة المرسل:", self.sender_job_label)
        f2.addRow("مسمى وظيفة المستلم:", self.receiver_job_label)
        main.addLayout(f2)

        main.addWidget(self._section_header("الوثيقة"))
        f3 = QFormLayout()
        f3.setSpacing(4)
        f3.setContentsMargins(0, 0, 0, 0)
        self.auth_doc_label = QLabel()
        self.auth_date_label = QLabel()
        self.created_label = QLabel()
        f3.addRow("رقم الوثيقة:", self.auth_doc_label)
        f3.addRow("تاريخ الوثيقة:", self.auth_date_label)
        f3.addRow("تاريخ الإنشاء:", self.created_label)
        main.addLayout(f3)

        main.addWidget(self._section_header("ملاحظات"))
        f4 = QFormLayout()
        f4.setSpacing(4)
        f4.setContentsMargins(0, 0, 0, 0)
        self.notes_label = QLabel()
        self.transport_label = QLabel()
        self.comments_label = QLabel()
        f4.addRow("ملاحظات:", self.notes_label)
        f4.addRow("معلومات النقل:", self.transport_label)
        f4.addRow("تعليقات إضافية:", self.comments_label)
        main.addLayout(f4)

        main.addWidget(self._section_header("العينات"))
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
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
            ],
        )
        h = self.items_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 6):
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setStyleSheet(TABLE_STYLE)
        main.addWidget(self.items_table)

        main.addWidget(self._section_header("المرفقات"))
        self.attachments_table = QTableWidget()
        self.attachments_table.setColumnCount(3)
        self.attachments_table.setHorizontalHeaderLabels(
            ["الملف", "النوع", "فتح"],
        )
        self.attachments_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )
        self.attachments_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )
        self.attachments_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )
        self.attachments_table.setAlternatingRowColors(True)
        self.attachments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attachments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.attachments_table.setStyleSheet(TABLE_STYLE)
        main.addWidget(self.attachments_table)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        print_btn = QPushButton("طباعة")
        print_btn.clicked.connect(self._print_pdf)
        btn_row.addWidget(print_btn)

        attach_btn = QPushButton("إرفاق ملف")
        attach_btn.clicked.connect(self._attach_file)
        btn_row.addWidget(attach_btn)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        main.addLayout(btn_row)

    def _load(self):
        receipt, items, atts = get_receipt(self.receipt_id)
        if not receipt:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الإيصال")
            self.reject()
            return

        self.title_label.setText(f"إيصال رقم: {receipt['receipt_no']}")
        ar_status = STATUS_TRANSLATION.get(receipt["status"], receipt["status"])
        self.status_label.setText(f"الحالة: {ar_status}")
        self.status_label.setStyleSheet(
            STATUS_STYLES.get(receipt["status"], "font-weight:bold;"),
        )

        self.tx_type_label.setText(receipt["tx_type"])
        self.sender_org_label.setText(receipt["sender_org"] or "-")
        self.receiver_org_label.setText(receipt["receiver_org"] or "-")
        self.sender_name_label.setText(receipt["sender_name"] or "-")
        self.receiver_name_label.setText(receipt["receiver_name"] or "-")
        self.sender_job_label.setText(receipt["sender_job_title"] or "-")
        self.receiver_job_label.setText(receipt["receiver_job_title"] or "-")
        self.auth_doc_label.setText(receipt["auth_doc_no"] or "-")
        self.auth_date_label.setText(receipt["auth_date"] or "-")
        self.created_label.setText(receipt["created_at"] or "-")
        self.notes_label.setText(receipt["notes"] or "-")
        self.transport_label.setText(receipt["transport_info"] or "-")
        self.comments_label.setText(receipt["additional_comments"] or "-")

        self.items_table.setRowCount(len(items))
        for i, item in enumerate(items):
            id = dict(item)
            self.items_table.setItem(
                i,
                0,
                QTableWidgetItem(id.get("sample_name", "")),
            )
            self.items_table.setItem(
                i,
                1,
                QTableWidgetItem(str(id["total_count"])),
            )
            self.items_table.setItem(
                i,
                2,
                QTableWidgetItem(str(id["valid_count"])),
            )
            self.items_table.setItem(
                i,
                3,
                QTableWidgetItem(str(id["damaged_count"])),
            )
            self.items_table.setItem(
                i,
                4,
                QTableWidgetItem(str(id["rejected_count"])),
            )
            self.items_table.setItem(
                i,
                5,
                QTableWidgetItem(str(id["non_conforming_count"])),
            )
            self.items_table.setItem(
                i,
                6,
                QTableWidgetItem(id.get("transport_condition", "")),
            )
            self.items_table.setItem(
                i,
                7,
                QTableWidgetItem(id.get("notes", "")),
            )

        self.attachments_table.setRowCount(len(atts))
        for i, att in enumerate(atts):
            self.attachments_table.setItem(
                i,
                0,
                QTableWidgetItem(Path(att["file_path"]).name),
            )
            self.attachments_table.setItem(
                i,
                1,
                QTableWidgetItem(att["file_type"]),
            )
            open_btn = QPushButton("فتح")
            file_path = att["file_path"]
            open_btn.clicked.connect(
                lambda _checked, fp=file_path: self._open_file(fp),
            )
            self.attachments_table.setCellWidget(i, 2, open_btn)

    def _print_pdf(self):
        receipt, _, _ = get_receipt(self.receipt_id)
        if not receipt:
            return
        try:
            rd = dict(receipt)
            path = generate_receipt_pdf(
                receipt_no=rd["receipt_no"],
                institution=rd.get("sender_org", ""),
                tx_type=rd.get("tx_type", ""),
                date_text=rd.get("created_at", ""),
            )
            log_action(
                self.current_user["id"],
                "receipt_printed",
                f"طباعة الإيصال: {receipt['receipt_no']}",
            )
            _open_file_safe(path)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل الطباعة: {e}")

    def _attach_file(self):
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملفاً",
            "",
            "بي دي إف (*.pdf);;صور (*.jpg *.jpeg *.png);;الكل (*)",
        )
        if not path:
            return
        try:
            save_attachment(self.receipt_id, path, "receipt_attachment")
            log_action(
                self.current_user["id"],
                "attachment_added",
                f"إرفاق ملف: {Path(path).name}",
            )
            toast(self, "تم إرفاق الملف", "success")
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل الإرفاق: {e}")

    @staticmethod
    def _open_file(file_path):
        try:
            _open_file_safe(file_path)
        except Exception:
            QMessageBox.warning(None, "خطأ", "تعذر فتح الملف")
