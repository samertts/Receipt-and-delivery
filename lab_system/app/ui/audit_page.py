from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.services.desktop_audit_service import DesktopAuditService
from lab_system.app.ui.page_header import PageHeader
from lab_system.app.utils.constants import TABLE_STYLE


class AuditPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self._audit_svc = DesktopAuditService()
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        header = PageHeader("سجل التدقيق", "جميع عمليات النظام المسجلة")
        self.layout().addWidget(header)

        header.add_action("تحديث", self.refresh, variant="secondary", tooltip="تحديث (F5)")

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الوقت", "المستخدم", "الإجراء", "الجهاز", "التفاصيل"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.layout().addWidget(self.table)

        self.refresh()

    def refresh(self):
        rows = self._audit_svc.list_logs(limit=200)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["timestamp"]))
            self.table.setItem(i, 1, QTableWidgetItem(str(r["user_id"])))
            self.table.setItem(i, 2, QTableWidgetItem(r["action"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["machine_name"]))
            self.table.setItem(i, 4, QTableWidgetItem(r["details"] or ""))
