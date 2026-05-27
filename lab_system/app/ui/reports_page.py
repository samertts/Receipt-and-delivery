from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.audit.logger import log_action
from lab_system.app.services.report_service import (
    export_receipts_csv,
    receipt_summary,
    sample_summary,
)


class ReportsPage(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._load()

    def _build_ui(self):
        title = QLabel("التقارير والإحصائيات")
        title.setStyleSheet("font-size:16px;font-weight:700;margin-bottom:10px;")
        self.layout().addWidget(title)

        filter_row = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        filter_row.addWidget(QLabel("من:"))
        filter_row.addWidget(self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(self.date_to.date().currentDate())
        filter_row.addWidget(QLabel("إلى:"))
        filter_row.addWidget(self.date_to)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self._load)
        filter_row.addWidget(refresh_btn)

        export_btn = QPushButton("تصدير CSV")
        export_btn.clicked.connect(self._export_csv)
        filter_row.addWidget(export_btn)

        self.layout().addLayout(filter_row)

        summary_group = QGroupBox("ملخص الإيصالات")
        summary_layout = QFormLayout(summary_group)
        self.total_label = QLabel("0")
        self.draft_label = QLabel("0")
        self.approved_label = QLabel("0")
        self.rejected_label = QLabel("0")
        self.archived_label = QLabel("0")
        self.cancelled_label = QLabel("0")
        summary_layout.addRow("الإجمالي:", self.total_label)
        summary_layout.addRow("مسودة:", self.draft_label)
        summary_layout.addRow("معتمد:", self.approved_label)
        summary_layout.addRow("مرفوض:", self.rejected_label)
        summary_layout.addRow("مؤرشف:", self.archived_label)
        summary_layout.addRow("ملغي:", self.cancelled_label)
        self.layout().addWidget(summary_group)

        samples_title = QLabel("تفاصيل العينات:")
        samples_title.setStyleSheet("font-weight:700;margin-top:10px;")
        self.layout().addWidget(samples_title)

        self.samples_table = QTableWidget()
        self.samples_table.setColumnCount(6)
        self.samples_table.setHorizontalHeaderLabels(
            [
                "نوع العينة",
                "المجموع",
                "صالح",
                "تالف",
                "مرفوض",
                "غير مطابق",
            ]
        )
        self.samples_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.layout().addWidget(self.samples_table)

    def _date_from(self):
        return self.date_from.date().toString("yyyy-MM-dd")

    def _date_to(self):
        return self.date_to.date().toString("yyyy-MM-dd")

    def _load(self):
        df = self._date_from()
        dt = self._date_to()
        summary = receipt_summary(date_from=df, date_to=dt)
        samples = sample_summary(date_from=df, date_to=dt)

        self.total_label.setText(str(summary["total"]))
        self.draft_label.setText(str(summary["by_status"].get("Draft", 0)))
        self.approved_label.setText(str(summary["by_status"].get("Approved", 0)))
        self.rejected_label.setText(str(summary["by_status"].get("Rejected", 0)))
        self.archived_label.setText(str(summary["by_status"].get("Archived", 0)))
        self.cancelled_label.setText(str(summary["by_status"].get("Cancelled", 0)))

        self.samples_table.setRowCount(len(samples))
        for i, s in enumerate(samples):
            self.samples_table.setItem(
                i, 0, QTableWidgetItem(s["sample_name"])
            )
            self.samples_table.setItem(
                i, 1, QTableWidgetItem(str(s["total"]))
            )
            self.samples_table.setItem(
                i, 2, QTableWidgetItem(str(s["valid"]))
            )
            self.samples_table.setItem(
                i, 3, QTableWidgetItem(str(s["damaged"]))
            )
            self.samples_table.setItem(
                i, 4, QTableWidgetItem(str(s["rejected"]))
            )
            self.samples_table.setItem(
                i, 5, QTableWidgetItem(str(s["non_conf"]))
            )

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ التقرير",
            f"تقرير_الإيصالات_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV (*.csv)",
        )
        if not path:
            return
        try:
            export_receipts_csv(
                path,
                date_from=self._date_from(),
                date_to=self._date_to(),
            )
            log_action(
                self.current_user["id"],
                "report_exported",
                f"تصدير تقرير: {path}",
            )
            QMessageBox.information(self, "نجاح", f"تم تصدير التقرير إلى {path}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل التصدير: {e}")
