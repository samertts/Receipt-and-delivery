
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

import shutil
from pathlib import Path

from lab_system.app.audit.logger import log_action
from lab_system.app.database import db as _db
from lab_system.app.services.backup_service import create_backup
from lab_system.app.services.recovery_service import verify_backup
from lab_system.app.settings.config import DB_PATH


class BackupPage(QWidget):
    def __init__(self, current_user) -> None:
        super().__init__()
        self.current_user = current_user
        self.setLayout(QVBoxLayout(self))
        self.setLayoutDirection(Qt.RightToLeft)

        title = QLabel("النسخ الاحتياطي والاستعادة")
        title.setStyleSheet("font-size:16px;font-weight:700;margin-bottom:10px;")
        self.layout().addWidget(title)

        btn_layout = QHBoxLayout()
        backup_btn = QPushButton("إنشاء نسخة احتياطية")
        backup_btn.clicked.connect(self._do_backup)
        btn_layout.addWidget(backup_btn)
        self.layout().addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["الملف", "التاريخ", "ملاحظات", "إجراءات"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout().addWidget(self.table)

        verify_all = QPushButton("التحقق من جميع النسخ الاحتياطية")
        verify_all.clicked.connect(self._verify_all)
        self.layout().addWidget(verify_all)

        self.refresh()

    def _do_backup(self):
        try:
            path = create_backup(user_id=self.current_user.get("id"))
            log_action(
                self.current_user["id"],
                "backup_created",
                f"نسخة احتياطية: {path}",
            )
            QMessageBox.information(self, "نجاح", "تم إنشاء النسخة الاحتياطية بنجاح")
            self.refresh()
        except Exception as e:
            QMessageBox.warning(
                self, "خطأ", f"فشل إنشاء النسخة الاحتياطية: {e}"
            )

    def refresh(self):
        with _db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM backups ORDER BY id DESC"
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
                lambda checked, fp=r["backup_file"]: self._verify(fp)
            )
            actions_layout.addWidget(verify_btn)

            restore_btn = QPushButton("استعادة")
            restore_btn.setStyleSheet("font-size:10pt;padding:4px;")
            restore_btn.clicked.connect(
                lambda checked, fp=r["backup_file"]: self._restore(fp)
            )
            actions_layout.addWidget(restore_btn)

            self.table.setCellWidget(i, 3, actions_widget)

    def _verify(self, backup_path):
        result = verify_backup(backup_path)
        if result["valid"]:
            QMessageBox.information(
                self, "تحقق", f"النسخة سليمة ({result['size']} بايت)"
            )
        else:
            QMessageBox.warning(
                self, "تحقق", f"النسخة تالفة: {result.get('error', 'خطأ غير معروف')}"
            )

    def _restore(self, backup_path):
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
            shutil.copy2(src, DB_PATH)
            log_action(
                self.current_user["id"],
                "backup_restored",
                f"استعادة من: {backup_path}",
            )
            QMessageBox.information(
                self, "نجاح", "تمت استعادة قاعدة البيانات. يرجى إعادة تشغيل التطبيق."
            )
        except Exception as e:
            QMessageBox.warning(
                self, "خطأ", f"فشلت الاستعادة: {e}"
            )

    def _verify_all(self):
        from lab_system.app.services.recovery_service import list_backups
        backups = list_backups()
        if not backups:
            QMessageBox.information(self, "تحقق", "لا توجد نسخ احتياطية")
            return
        valid = 0
        invalid = 0
        for b in backups:
            result = verify_backup(b["path"])
            if result["valid"]:
                valid += 1
            else:
                invalid += 1
        QMessageBox.information(
            self,
            "نتيجة التحقق",
            f"النسخ السليمة: {valid}\nالنسخ التالفة: {invalid}\nالمجموع: {len(backups)}",
        )
