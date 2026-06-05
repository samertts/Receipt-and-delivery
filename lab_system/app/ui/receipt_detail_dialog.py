import subprocess
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

STATUS_STYLES = {
    "Draft": "color:#6B7280;font-weight:bold;",
    "Approved": "color:#059669;font-weight:bold;",
    "Rejected": "color:#DC2626;font-weight:bold;",
    "Archived": "color:#D97706;font-weight:bold;",
    "Cancelled": "color:#6B7280;font-weight:bold;",
}


class ReceiptDetailDialog(QDialog):
    def __init__(self, current_user, receipt_id):
        super().__init__()
        self.current_user = current_user
        self.receipt_id = receipt_id
        self.setWindowTitle("تفاصيل الإيصال")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._load()

    def _build_ui(self):
        main = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size:16px;font-weight:700;")
        main.addWidget(self.title_label)

        self.status_label = QLabel()
        main.addWidget(self.status_label)

        details_form = QFormLayout()
        self.sender_org_label = QLabel()
        self.receiver_org_label = QLabel()
        self.sender_name_label = QLabel()
        self.receiver_name_label = QLabel()
        self.sender_job_label = QLabel()
        self.receiver_job_label = QLabel()
        self.auth_doc_label = QLabel()
        self.auth_date_label = QLabel()
        self.tx_type_label = QLabel()
        self.created_label = QLabel()
        self.notes_label = QLabel()
        self.transport_label = QLabel()
        self.comments_label = QLabel()

        details_form.addRow("نوع المعاملة:", self.tx_type_label)
        details_form.addRow("الجهة المرسلة:", self.sender_org_label)
        details_form.addRow("الجهة المستقبلة:", self.receiver_org_label)
        details_form.addRow("اسم المرسل:", self.sender_name_label)
        details_form.addRow("اسم المستلم:", self.receiver_name_label)
        details_form.addRow("مسمى وظيفة المرسل:", self.sender_job_label)
        details_form.addRow("مسمى وظيفة المستلم:", self.receiver_job_label)
        details_form.addRow("رقم الوثيقة:", self.auth_doc_label)
        details_form.addRow("تاريخ الوثيقة:", self.auth_date_label)
        details_form.addRow("تاريخ الإنشاء:", self.created_label)
        details_form.addRow("ملاحظات:", self.notes_label)
        details_form.addRow("معلومات النقل:", self.transport_label)
        details_form.addRow("تعليقات إضافية:", self.comments_label)
        main.addLayout(details_form)

        items_title = QLabel("العينات:")
        items_title.setStyleSheet("font-weight:700;margin-top:10px;")
        main.addWidget(items_title)

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
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch,
        )
        main.addWidget(self.items_table)

        atts_title = QLabel("المرفقات:")
        atts_title.setStyleSheet("font-weight:700;margin-top:10px;")
        main.addWidget(atts_title)

        self.attachments_table = QTableWidget()
        self.attachments_table.setColumnCount(3)
        self.attachments_table.setHorizontalHeaderLabels(
            ["الملف", "النوع", "فتح"],
        )
        self.attachments_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch,
        )
        main.addWidget(self.attachments_table)

        btn_row = QHBoxLayout()
        print_btn = QPushButton("طباعة PDF")
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
        self.status_label.setText(f"الحالة: {receipt['status']}")
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
                i, 0, QTableWidgetItem(id.get("sample_name", "")),
            )
            self.items_table.setItem(
                i, 1, QTableWidgetItem(str(id["total_count"])),
            )
            self.items_table.setItem(
                i, 2, QTableWidgetItem(str(id["valid_count"])),
            )
            self.items_table.setItem(
                i, 3, QTableWidgetItem(str(id["damaged_count"])),
            )
            self.items_table.setItem(
                i, 4, QTableWidgetItem(str(id["rejected_count"])),
            )
            self.items_table.setItem(
                i, 5, QTableWidgetItem(str(id["non_conforming_count"])),
            )
            self.items_table.setItem(
                i, 6, QTableWidgetItem(id.get("transport_condition", "")),
            )
            self.items_table.setItem(
                i, 7, QTableWidgetItem(id.get("notes", "")),
            )

        self.attachments_table.setRowCount(len(atts))
        for i, att in enumerate(atts):
            self.attachments_table.setItem(
                i, 0, QTableWidgetItem(Path(att["file_path"]).name),
            )
            self.attachments_table.setItem(
                i, 1, QTableWidgetItem(att["file_type"]),
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
            subprocess.Popen([str(path)], shell=False)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل الطباعة: {e}")

    def _attach_file(self):
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملفاً",
            "",
            "PDF (*.pdf);;Images (*.jpg *.jpeg *.png);;All (*)",
        )
        if not path:
            return
        try:
            save_attachment(self.receipt_id, path, "receipt_attachment")
            log_action(
                self.current_user["id"],
                "attachment_added",
                f"إرفاق ملف: {path}",
            )
            QMessageBox.information(self, "نجاح", "تم إرفاق الملف")
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل الإرفاق: {e}")

    @staticmethod
    def _open_file(file_path):
        try:
            subprocess.Popen([str(file_path)], shell=False)
        except Exception:
            QMessageBox.warning(None, "خطأ", "تعذر فتح الملف")
