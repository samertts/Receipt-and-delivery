from PySide6.QtCore import QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


TOAST_DURATION = 3500


class ToastNotification(QFrame):
    _instance = None
    _active_toasts = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedWidth(380)
        self._timeout = TOAST_DURATION

        self._container = QFrame(self)
        self._container.setObjectName("ToastContainer")
        self._container.setStyleSheet("""
            #ToastContainer {
                background: #1E293B; border-radius: 10px;
                padding: 14px 18px;
            }
        """)
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(10)

        self._icon_label = QLabel()
        self._icon_label.setStyleSheet("font-size:18px;")
        self._layout.addWidget(self._icon_label)

        self._text_label = QLabel()
        self._text_label.setStyleSheet("color:#F1F5F9;font-size:12pt;font-weight:500;")
        self._text_label.setWordWrap(True)
        self._layout.addWidget(self._text_label, 1)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(24, 24)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #94A3B8;
                border: none; font-size:14px;
            }
            QPushButton:hover { color: #F1F5F9; }
        """)
        self._close_btn.clicked.connect(self._dismiss)
        self._layout.addWidget(self._close_btn)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._container)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._dismiss)

        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(250)

    def show_toast(self, text, toast_type="info", duration=None):
        self._text_label.setText(text)
        if duration:
            self._timeout = duration

        colors = {
            "success": ("✅", "#059669"),
            "error": ("❌", "#DC2626"),
            "warning": ("⚠️", "#D97706"),
            "info": ("ℹ️", "#2563EB"),
        }
        icon, border_color = colors.get(toast_type, colors["info"])
        self._icon_label.setText(icon)
        self._container.setStyleSheet(f"""
            #ToastContainer {{
                background: #1E293B; border-radius: 10px;
                padding: 14px 18px;
                border-left: 4px solid {border_color};
            }}
        """)
        self.adjustSize()
        self._position()
        self.show()
        self.setWindowOpacity(0.0)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.start()
        self._timer.start(self._timeout)

    def _position(self):
        parent = self.parent()
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 20
        else:
            x = 20
            y = 20
        offset = 0
        for t in ToastNotification._active_toasts:
            if t is not self:
                offset += t.height() + 10
        self.move(x, y + offset)

    def _dismiss(self):
        self._timer.stop()
        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(self.windowOpacity())
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.finished.connect(self._close)
        self._opacity_anim.start()

    def _close(self):
        if self in ToastNotification._active_toasts:
            ToastNotification._active_toasts.remove(self)
        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        if self not in ToastNotification._active_toasts:
            ToastNotification._active_toasts.append(self)

    def closeEvent(self, event):
        if self in ToastNotification._active_toasts:
            ToastNotification._active_toasts.remove(self)
        super().closeEvent(event)


def toast(parent, text, toast_type="info", duration=TOAST_DURATION):
    t = ToastNotification(parent)
    t.show_toast(text, toast_type, duration)
    return t
