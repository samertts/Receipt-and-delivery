from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.database import db as _db
from lab_system.app.ui.page_header import PageHeader


class AuditPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        header = PageHeader("سجل التدقيق", "جميع عمليات النظام المسجلة")
        self.layout().addWidget(header)

        refresh_btn = header.add_action("تحديث", self.refresh, variant="secondary", tooltip="تحديث (F5)")

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الوقت", "المستخدم", "الإجراء", "الجهاز", "التفاصيل"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.layout().addWidget(self.table)

        self.refresh()

    def refresh(self):
        with _db.get_conn() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200").fetchall()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["timestamp"]))
            self.table.setItem(i, 1, QTableWidgetItem(str(r["user_id"])))
            self.table.setItem(i, 2, QTableWidgetItem(r["action"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["machine_name"]))
            self.table.setItem(i, 4, QTableWidgetItem(r["details"] or ""))
