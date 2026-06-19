from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from lab_system.app.utils.constants import THEME


class LoadingOverlay(QWidget):
    def __init__(self, parent=None, text="جاري التحميل..."):
        super().__init__(parent)
        self._text = text
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if parent:
            self.setGeometry(parent.rect())

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self._label = QLabel(text)
        self._label.setStyleSheet(f"""
            color: {THEME["primary"]}; font-size: 14pt;
            font-weight: 600; background: transparent;
        """)
        self._label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label)

    def _rotate(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def start(self):
        self.show()
        self.raise_()
        self._timer.start(50)

    def stop(self):
        self._timer.stop()
        self.hide()

    def set_text(self, text):
        self._label.setText(text)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(255, 255, 255, 180))

        center = self.rect().center()
        p.translate(center)
        p.rotate(self._angle)

        colors = [THEME["primary"], THEME["secondary"], THEME["success"]]
        for i, color_str in enumerate(colors):
            p.setBrush(QColor(color_str))
            p.setPen(Qt.NoPen)
            x = -30 + i * 25
            alpha = 255 - (i * 60)
            c = QColor(color_str)
            c.setAlpha(max(alpha, 60))
            p.setBrush(c)
            p.drawRoundedRect(x, -6, 16, 12, 4, 4)

        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
