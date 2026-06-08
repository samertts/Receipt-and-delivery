
import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.auth.permissions import check_permission
from lab_system.app.audit.logger import log_action
from lab_system.app.database import db as _db
from lab_system.app.services.backup_service import create_backup
from lab_system.app.services.recovery_service import verify_backup
from lab_system.app.settings.config import DB_PATH
from lab_system.app.ui.notifications import toast
from lab_system.app.ui.page_header import PageHeader


class BackupPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        header = PageHeader("النسخ الاحتياطي والاستعادة", "إدارة وحماية بيانات النظام")
        self.layout().addWidget(header)

        header.add_action("إنشاء نسخة احتياطية", self._do_backup)
        header.add_action("التحقق من الكل", self._verify_all, variant="secondary")

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["الملف", "التاريخ", "ملاحظات", "إجراءات"],
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.layout().addWidget(self.table)

        self.refresh()

    def _do_backup(self):
        check_permission(self.current_user, 'backup.create')
        from pathlib import Path
        try:
            path = create_backup(user_id=self.current_user.get("id"))
            log_action(
                self.current_user["id"],
                "backup_created",
                f"نسخة احتياطية: {Path(path).name}",
            )
        except Exception as e:
            QMessageBox.warning(
                self, "خطأ", f"فشل إنشاء النسخة الاحتياطية: {e}",
            )

    def refresh(self):
        with _db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM backups ORDER BY id DESC",
            ).fetchall()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["backup_file"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["created_at"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["notes"] or ""))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            verify_btn = QPushButton("تحقق")
            verify_btn.setStyleSheet("font-size:10pt;padding:4px;")
            verify_btn.clicked.connect(
                lambda _checked, fp=r["backup_file"]: self._verify(fp),
            )
            actions_layout.addWidget(verify_btn)

            restore_btn = QPushButton("استعادة")
            restore_btn.setStyleSheet("font-size:10pt;padding:4px;")
            restore_btn.clicked.connect(
                lambda _checked, fp=r["backup_file"]: self._restore(fp),
            )
            actions_layout.addWidget(restore_btn)

            self.table.setCellWidget(i, 3, actions_widget)

    def _verify(self, backup_path):
        result = verify_backup(backup_path)
        if result["valid"]:
            toast(self, "تم إنشاء النسخة الاحتياطية", "success")
        else:
            QMessageBox.warning(
                self, "تحقق", f"النسخة تالفة: {result.get('error', 'خطأ غير معروف')}",
            )

    def _restore(self, backup_path):
        check_permission(self.current_user, 'backup.restore')
        reply = QMessageBox.question(
            self,
            "تأكيد الاستعادة",
            "هل أنت متأكد؟ سيتم استبدال قاعدة البيانات الحالية بالنسخة الاحتياطية.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            src = Path(backup_path)
            if not src.exists():
                raise FileNotFoundError(f"ملف النسخة غير موجود: {backup_path}")
            result = verify_backup(backup_path)
            if not result.get("valid"):
                raise ValueError(f"النسخة تالفة: {result.get('error', 'خطأ غير معروف')}")
            shutil.copy2(src, DB_PATH)
            log_action(
                self.current_user["id"],
                "backup_restored",
                f"استعادة من: {Path(backup_path).name}",
            )
            toast(self, "تم التحقق بنجاح", "success")
        except Exception as e:
            QMessageBox.warning(
                self, "خطأ", f"فشلت الاستعادة: {e}",
            )

    def _verify_all(self):
        from lab_system.app.services.recovery_service import list_backups
        backups = list_backups()
        if not backups:
            toast(self, "لا توجد نسخ احتياطية", "warning")
            return
        valid = 0
        invalid = 0
        for b in backups:
            result = verify_backup(b["path"])
            if result["valid"]:
                valid += 1
            else:
                invalid += 1
        toast(self, "تمت الاستعادة بنجاح", "success")
