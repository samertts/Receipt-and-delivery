from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.database import db as _db
from lab_system.app.diagnostics.startup import run_all_checks
from lab_system.app.settings.config import CONFIG
from lab_system.app.sync.service import sync_service
from lab_system.app.utils.constants import THEME, TABLE_STYLE

ROLE_MAP = {
    "Admin": "مدير النظام",
    "Supervisor": "مشرف",
    "User": "مستخدم",
    "Auditor": "مدقق",
}


class StatCard(QFrame):
    def __init__(self, label, value, color=THEME['primary'], icon=""):
        super().__init__()
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            #StatCard {{
                background: {THEME['panel']};
                border: 1px solid {THEME['border']};
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size:28px;font-weight:800;color:{color};")
        layout.addWidget(self.value_label)

        self.label_label = QLabel(f"{icon} {label}" if icon else label)
        self.label_label.setStyleSheet("font-size:11pt;color:#64748B;")
        layout.addWidget(self.label_label)


class DashboardPage(QWidget):
    def __init__(self, user, auth_service=None, navigate_cb=None) -> None:
        super().__init__()
        self._auth = auth_service
        self.current_user = user
        self._navigate_cb = navigate_cb
        self.setLayout(QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setLayoutDirection(Qt.RightToLeft)

        welcome = QLabel(f"مرحباً {user['full_name']}")
        welcome.setStyleSheet("font-size:20px;font-weight:700;color:#0F172A;")
        self.layout().addWidget(welcome)

        role_text = ROLE_MAP.get(user["role"], user["role"])
        subtitle = QLabel(f"الصلاحية: {role_text}  |  الإصدار {CONFIG.app_version}")
        subtitle.setStyleSheet("font-size:11pt;color:#64748B;margin-bottom:16px;")
        self.layout().addWidget(subtitle)

        self._build_stats_grid()

        if self._auth and self._auth.needs_password_change():
            warn = QLabel("⚠ يرجى تغيير كلمة المرور الافتراضية")
            warn.setStyleSheet("color:#DC2626;font-weight:bold;font-size:14px;padding:12px;background:#FEF2F2;border-radius:8px;")
            self.layout().addWidget(warn)

        self._build_quick_actions()

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        bottom.addWidget(self._build_recent_activity_box(), 2)
        right_col = QVBoxLayout()
        right_col.setSpacing(12)
        right_col.addWidget(self._build_backups_box())
        right_col.addWidget(self._build_sync_health_box())
        bottom.addLayout(right_col, 1)
        self.layout().addLayout(bottom)

        self._build_health_status()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        grid = None
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and isinstance(item, QGridLayout):
                grid = item
                break
        if grid:
            cols = max(2, min(4, event.size().width() // 280))
            current_cols = grid.columnCount()
            if current_cols != cols:
                widgets = []
                for r in range(grid.rowCount()):
                    for c in range(grid.columnCount()):
                        w = grid.itemAtPosition(r, c)
                        if w and w.widget():
                            widgets.append(w.widget())
                for i, w in enumerate(widgets):
                    grid.addWidget(w, i // cols, i % cols)
                for c in range(cols):
                    grid.setColumnStretch(c, 1)

    def _build_stats_grid(self):
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        with _db.get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
            today_count = conn.execute(
                "SELECT COUNT(*) FROM receipts WHERE date(created_at) = ?", (today,)
            ).fetchone()[0]
            week_count = conn.execute(
                "SELECT COUNT(*) FROM receipts WHERE date(created_at) >= ?", (week_ago,)
            ).fetchone()[0]
            month_count = conn.execute(
                "SELECT COUNT(*) FROM receipts WHERE date(created_at) >= ?", (month_ago,)
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM receipts WHERE status = 'Draft'"
            ).fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM receipts WHERE status = 'Approved'"
            ).fetchone()[0]
            org_count = conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

        grid = QGridLayout()
        grid.setSpacing(12)

        cards = [
            ("إجمالي الاستلامات", total, THEME['primary'], "📦"),
            ("استلامات اليوم", today_count, THEME['success'], "📅"),
            ("آخر 7 أيام", week_count, "#D97706", "📊"),
            ("آخر 30 يوماً", month_count, "#7C3AED", "📈"),
            ("قيد المعالجة", pending, THEME['warning'], "⏳"),
            ("المكتملة", completed, THEME['success'], "✅"),
            ("الجهات", org_count, "#0891B2", "🏛️"),
            ("المستخدمون", user_count, "#DC2626", "👥"),
        ]

        cols = 4
        for i, (label, value, color, icon) in enumerate(cards):
            card = StatCard(label, value, color, icon)
            grid.addWidget(card, i // cols, i % cols)
        for c in range(cols):
            grid.setColumnStretch(c, 1)

        self.layout().addLayout(grid)

    def _build_quick_actions(self):
        section = QLabel("إجراءات سريعة")
        section.setStyleSheet("font-size:14px;font-weight:700;color:#0F172A;margin-top:16px;margin-bottom:8px;")
        self.layout().addWidget(section)

        row = QHBoxLayout()
        row.setSpacing(8)

        actions = [
            ("استلام جديد", lambda: self._navigate_cb and self._navigate_cb("receipts")),
            ("التقارير", lambda: self._navigate_cb and self._navigate_cb("reports")),
            ("إدارة الجهات", lambda: self._navigate_cb and self._navigate_cb("orgs")),
            ("المستخدمون", lambda: self._navigate_cb and self._navigate_cb("users")),
        ]
        for text, cb in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {THEME['panel']}; color: #334155;
                    border: 1px solid {THEME['border']}; border-radius: 8px;
                    padding: 12px 20px; font-size: 12pt; min-height: 44px;
                }}
                QPushButton:hover {{
                    background: #F1F5F9; border-color: {THEME['primary']};
                }}
            """)
            if cb:
                btn.clicked.connect(cb)
            row.addWidget(btn)

        self.layout().addLayout(row)

    def _build_recent_activity_box(self):
        box = QGroupBox("آخر النشاطات")
        layout = QVBoxLayout(box)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["الوقت", "المستخدم", "الإجراء"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumHeight(200)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(TABLE_STYLE)

        with _db.get_conn() as conn:
            rows = conn.execute(
                "SELECT timestamp, user_id, action FROM audit_logs ORDER BY id DESC LIMIT 10"
            ).fetchall()

        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r["timestamp"]))
            table.setItem(i, 1, QTableWidgetItem(str(r["user_id"])))
            table.setItem(i, 2, QTableWidgetItem(r["action"]))

        layout.addWidget(table)
        return box

    def _build_backups_box(self):
        box = QGroupBox("آخر النسخ الاحتياطية")
        layout = QVBoxLayout(box)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["التاريخ", "الحالة"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumHeight(200)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(TABLE_STYLE)

        with _db.get_conn() as conn:
            rows = conn.execute(
                "SELECT created_at, notes FROM backups ORDER BY id DESC LIMIT 5"
            ).fetchall()

        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r["created_at"]))
            table.setItem(i, 1, QTableWidgetItem(r["notes"] or "ناجح"))

        layout.addWidget(table)
        return box

    def _build_sync_health_box(self):
        box = QGroupBox("حالة المزامنة")
        layout = QVBoxLayout(box)
        health = sync_service.get_health()
        status = QLabel()
        if not health['enabled']:
            status.setText("⚙ المزامنة غير مفعلة")
            status.setStyleSheet("color:#6B7280;font-weight:bold;padding:8px;")
        elif health['healthy']:
            status.setText(f"✓ سليمة — {health['synced']} عناصر متزامنة")
            status.setStyleSheet(f"color:{THEME['success']};font-weight:bold;padding:8px;")
        else:
            status.setText(f"⚠ {health['pending']} معلقة, {health['conflicts']} تعارض")
            status.setStyleSheet(f"color:{THEME['warning']};font-weight:bold;padding:8px;")
        layout.addWidget(status)
        return box

    def _build_health_status(self):
        diag = run_all_checks()
        health = QLabel()
        if diag["all_ok"]:
            health.setText("✓ جميع الأنظمة تعمل بشكل طبيعي")
            health.setStyleSheet(f"color:{THEME['success']};font-weight:bold;padding:12px;background:#F0FDF4;border-radius:8px;margin-top:8px;")
        else:
            health.setText("⚠ توجد مشكلات في النظام — راجع سجل التشخيص")
            health.setStyleSheet(f"color:{THEME['warning']};font-weight:bold;padding:12px;background:#FFFBEB;border-radius:8px;margin-top:8px;")
        self.layout().addWidget(health)
