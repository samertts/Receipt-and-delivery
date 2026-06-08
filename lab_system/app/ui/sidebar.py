from PySide6.QtCore import QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lab_system.app.ui.icons import (
    icon_audit,
    icon_backup,
    icon_dashboard,
    icon_organizations,
    icon_receipts,
    icon_reports,
    icon_samples,
    icon_settings,
    icon_statistics,
    icon_users,
)
from lab_system.app.utils.constants import THEME


SIDEBAR_COLLAPSED = 64
SIDEBAR_EXPANDED = 260
SIDEBAR_BG = QColor(THEME['sidebar_bg'])
SIDEBAR_ITEM_HOVER = QColor(THEME['sidebar_hover'])
SIDEBAR_ITEM_ACTIVE = QColor(THEME['sidebar_active'])
SIDEBAR_ACCENT = QColor(THEME['primary'])
SIDEBAR_TEXT = QColor(THEME['sidebar_text'])
SIDEBAR_TEXT_ACTIVE = QColor(THEME['sidebar_active_text'])
SIDEBAR_GROUP_TEXT = QColor(THEME['sidebar_text'])
SIDEBAR_HEADER_BG = QColor('#0B1628')


class SidebarItem(QWidget):
    clicked = Signal(str)

    def __init__(self, key, label, icon_fn, parent=None):
        super().__init__(parent)
        self._key = key
        self._label = label
        self._icon_fn = icon_fn
        self._active = False
        self._hovered = False
        self._collapsed = False
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

    def set_active(self, active):
        self._active = active
        self.update()

    def set_collapsed(self, collapsed):
        self._collapsed = collapsed
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if self._active:
            p.fillRect(0, 0, w, h, SIDEBAR_ITEM_ACTIVE)
            p.fillRect(0, 0, 3, h, SIDEBAR_ACCENT)
        elif self._hovered:
            p.fillRect(0, 0, w, h, SIDEBAR_ITEM_HOVER)

        icon_size = 20
        icon_x = 22 if not self._collapsed else (w - icon_size) // 2
        icon_y = (h - icon_size) // 2

        color = SIDEBAR_TEXT_ACTIVE if self._active else SIDEBAR_TEXT
        icon = self._icon_fn(color)
        icon.paint(p, icon_x, icon_y, icon_size, icon_size)

        if not self._collapsed:
            text_x = 52
            text_y = (h + 5) // 2
            p.setPen(color)
            f = QFont()
            f.setPointSize(10)
            if self._active:
                f.setBold(True)
            p.setFont(f)
            p.drawText(text_x, text_y, self._label)

        p.end()

    @property
    def key(self):
        return self._key


class SidebarGroup(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_collapsed(self, collapsed):
        self._collapsed = collapsed
        self.update()

    def paintEvent(self, event):
        if self._collapsed:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        text_x = 16
        text_y = (self.height() + 5) // 2
        p.setPen(SIDEBAR_GROUP_TEXT)
        f = QFont()
        f.setPointSize(8)
        f.setBold(True)
        p.setFont(f)
        p.drawText(text_x, text_y, self._title.upper())
        p.end()


class SidebarHeader(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

    def set_collapsed(self, collapsed):
        self._collapsed = collapsed
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._collapsed = not self._collapsed
            self.toggled.emit(self._collapsed)
            self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(0, 0, self.width(), self.height(), SIDEBAR_HEADER_BG)

        if not self._collapsed:
            f = QFont()
            f.setPointSize(11)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor('#FFFFFF'))
            p.drawText(16, 34, "الاستلام المختبري")

            f2 = QFont()
            f2.setPointSize(7)
            p.setFont(f2)
            p.setPen(SIDEBAR_GROUP_TEXT)
            p.drawText(16, 49, "نظام الاستلام والتسليم المختبري")
        else:
            f = QFont()
            f.setPointSize(14)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor('#FFFFFF'))
            p.drawText(0, 0, self.width(), self.height(), Qt.AlignCenter, "م")

        # Toggle button area
        toggle_x = self.width() - 32
        toggle_y = 20
        p.setPen(QPen(SIDEBAR_GROUP_TEXT, 2))
        if not self._collapsed:
            p.drawLine(toggle_x, toggle_y, toggle_x - 8, toggle_y + 8)
            p.drawLine(toggle_x, toggle_y + 16, toggle_x - 8, toggle_y + 8)
        else:
            p.drawLine(toggle_x, toggle_y, toggle_x + 8, toggle_y + 8)
            p.drawLine(toggle_x, toggle_y + 16, toggle_x + 8, toggle_y + 8)

        p.end()


class ModernSidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._current_key = None
        self._items = []
        self._item_widgets = {}

        self.setObjectName("ModernSidebar")
        self.setFixedWidth(SIDEBAR_EXPANDED)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = SidebarHeader()
        self.header.toggled.connect(self._toggle)
        layout.addWidget(self.header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }"
                             "QScrollBar:vertical { width: 4px; background: #1E293B; }"
                             "QScrollBar::handle:vertical { background: #475569; border-radius: 2px; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 8, 0, 8)
        self._content_layout.setSpacing(0)

        PERM_MAP = {
            "dashboard": "dashboard.view",
            "receipts": "receipts.read",
            "orgs": "organizations.read",
            "users": "users.read",
            "audit": "audit.read",
            "reports": "reports.read",
            "backup": "backup.create",
            "settings": "settings.read",
            "samples": "receipts.read",
            "statistics": "reports.export",
        }

        groups = [
            ("العمليات", [
                ("dashboard", "لوحة التحكم", icon_dashboard),
                ("receipts", "الاستلامات", icon_receipts),
                ("orgs", "المؤسسات", icon_organizations),
                ("samples", "العينات", icon_samples),
            ]),
            ("الإدارة", [
                ("users", "المستخدمون", icon_users),
                ("audit", "سجل التدقيق", icon_audit),
            ]),
            ("التقارير", [
                ("reports", "التقارير", icon_reports),
                ("statistics", "الإحصائيات", icon_statistics),
            ]),
            ("النظام", [
                ("backup", "النسخ الاحتياطي", icon_backup),
                ("settings", "الإعدادات", icon_settings),
            ]),
        ]

        from lab_system.app.auth.permissions import check_permission

        first_group = True
        for group_title, items in groups:
            if not first_group:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("background: #334155; max-height: 1px; margin: 4px 16px;")
                sep.setFixedHeight(1)
                self._content_layout.addWidget(sep)
            first_group = False

            group = SidebarGroup(group_title)
            self._content_layout.addWidget(group)

            for key, label, icon_fn in items:
                perm = PERM_MAP.get(key)
                if perm:
                    try:
                        check_permission(user, perm)
                    except Exception:
                        continue
                item = SidebarItem(key, label, icon_fn)
                item.clicked.connect(self._on_item_clicked)
                self._content_layout.addWidget(item)
                self._items.append(key)
                self._item_widgets[key] = item

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.setStyleSheet("""
            #ModernSidebar {
                background-color: #1E293B;
                border-right: 1px solid #334155;
            }
        """)

    def _on_item_clicked(self, key):
        self.set_active(key)
        self.page_changed.emit(key)

    def set_active(self, key):
        self._current_key = key
        for k, w in self._item_widgets.items():
            w.set_active(k == key)

    def _toggle(self, collapsed):
        self._collapsed = collapsed
        self.animate_width(SIDEBAR_COLLAPSED if collapsed else SIDEBAR_EXPANDED)
        for w in self._item_widgets.values():
            w.set_collapsed(collapsed)
        for i in range(self._content_layout.count()):
            item = self._content_layout.itemAt(i)
            if item and item.widget():
                if isinstance(item.widget(), SidebarGroup):
                    item.widget().set_collapsed(collapsed)
        self.header.set_collapsed(collapsed)

    def animate_width(self, target_width):
        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(200)
        anim.setStartValue(self.width())
        anim.setEndValue(target_width)
        anim.start()
        self._anim = anim
        self.setFixedWidth(target_width)
        self.update()

    @property
    def current_key(self):
        return self._current_key

    @property
    def items(self):
        return self._items
