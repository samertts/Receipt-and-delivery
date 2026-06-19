from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PageHeader(QWidget):
    def __init__(self, title, description="", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(12)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size:18px;font-weight:700;color:#0F172A;")
        texts.addWidget(self.title_label)

        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setStyleSheet("font-size:11pt;color:#64748B;")
            texts.addWidget(self.desc_label)

        top.addLayout(texts, 1)

        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(8)
        top.addLayout(self.action_layout)

        layout.addLayout(top)

    def add_action(
        self, text, callback=None, icon=None, variant="primary", tooltip=None
    ):
        btn = QPushButton(text)
        if tooltip:
            btn.setToolTip(tooltip)
        if variant == "secondary":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9; color: #334155;
                    border: 1px solid #CBD5E1; border-radius: 6px;
                    padding: 8px 16px; min-height: 36px; font-size: 12pt;
                }
                QPushButton:hover { background-color: #E2E8F0; }
            """)
        elif variant == "danger":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626; color: white;
                    border: none; border-radius: 6px;
                    padding: 8px 16px; min-height: 36px; font-size: 12pt;
                }
                QPushButton:hover { background-color: #B91C1C; }
            """)
        if callback:
            btn.clicked.connect(callback)
        self.action_layout.addWidget(btn)
        return btn

    def add_search(self, placeholder="بحث..."):
        search = QLineEdit()
        search.setPlaceholderText(f"🔍 {placeholder}")
        search.setToolTip("بحث (Ctrl+F)")
        search.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC; border: 1px solid #CBD5E1;
                border-radius: 6px; min-height: 36px;
                padding: 4px 12px 4px 36px; font-size: 12pt;
            }
            QLineEdit:focus { border: 2px solid #2563EB; }
        """)
        self.action_layout.addWidget(search)
        return search
