from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from lab_system.app.utils.constants import THEME


PRIMARY = QColor(THEME['primary'])
MUTED = QColor(THEME['muted'])
WHITE = QColor('#FFFFFF')
SIDEBAR_BG = QColor(THEME['sidebar_bg'])
SIDEBAR_TEXT = QColor(THEME['sidebar_text'])
SIDEBAR_ACTIVE = QColor(THEME['primary'])
SIDEBAR_HOVER = QColor(THEME['sidebar_hover'])
SIDEBAR_GROUP = QColor(THEME['sidebar_text'])


def _paint_icon(draw_fn, size=24, color=PRIMARY):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color, 2))
    painter.setBrush(color)
    draw_fn(painter, size)
    painter.end()
    return QIcon(pixmap)


def icon_dashboard(color=PRIMARY):
    def draw(p, s):
        m = 4
        p.drawRect(m, m, s//2 - m, s//2 - m)
        p.drawRect(s//2 + 1, m, s//2 - m - 1, s//2 - m)
        p.drawRect(m, s//2 + 1, s//2 - m, s//2 - m - 1)
        p.drawRect(s//2 + 1, s//2 + 1, s//2 - m - 1, s//2 - m - 1)
    return _paint_icon(draw, color=color)


def icon_receipts(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawRect(4, 2, s-8, s-4)
        p.drawLine(8, s//2 - 2, s-8, s//2 - 2)
        p.drawLine(8, s//2 + 3, s-8, s//2 + 3)
        p.drawLine(s//2 - 4, s//2 - 2, s//2 - 4, s-4)
    return _paint_icon(draw, color=color)


def icon_organizations(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawRect(3, s//2 + 1, s//2 - 3, s//2 - 4)
        p.drawRect(s//2 + 1, s//2 + 1, s//2 - 4, s//2 - 4)
        p.drawRect(s//4 + 2, 2, s//2, s//2)
    return _paint_icon(draw, color=color)


def icon_users(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(s//2 - 4, 3, 8, 8)
        p.drawArc(3, s//2 - 2, s-6, s//2, 0, 180*16)
    return _paint_icon(draw, color=color)


def icon_reports(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawRect(3, 2, s-6, s-4)
        p.drawLine(s-6, 10, s-6, s-6)
        p.drawLine(6, s//2 + 4, s-9, s//2 + 4)
        p.drawLine(6, s//2 + 10, s-9, s//2 + 10)
    return _paint_icon(draw, color=color)


def icon_settings(color=PRIMARY):
    def draw(p, s):
        center = s // 2
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center-4, center-4, 8, 8)
        for i in range(4):
            a = i * 45 + 22
            import math
            rad = math.radians(a)
            x1 = center + int(6 * math.cos(rad))
            y1 = center + int(6 * math.sin(rad))
            x2 = center + int(10 * math.cos(rad))
            y2 = center + int(10 * math.sin(rad))
            p.drawLine(x1, y1, x2, y2)
    return _paint_icon(draw, color=color)


def icon_audit(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawRect(3, 2, s-6, s-4)
        for i in range(3):
            y = 6 + i * (s - 10) // 2
            p.drawLine(6, y, s-6, y)
    return _paint_icon(draw, color=color)


def icon_backup(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(s//2, s//2, s//2 - 2, s//2 - 2)
        p.drawLine(s//4, s//4, s//2, s//2)
        p.drawLine(s//2, s//2, 3*s//4, s//4)
    return _paint_icon(draw, color=color)


def icon_chevron_left(color=MUTED):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawLine(s*3//4, s//4, s//4, s//2)
        p.drawLine(s//4, s//2, s*3//4, s*3//4)
    return _paint_icon(draw, color=color)


def icon_chevron_right(color=MUTED):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawLine(s//4, s//4, s*3//4, s//2)
        p.drawLine(s*3//4, s//2, s//4, s*3//4)
    return _paint_icon(draw, color=color)


def icon_search(color=MUTED):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(3, 3, s//2, s//2)
        p.drawLine(s//2 + 2, s//2 + 2, s-4, s-4)
    return _paint_icon(draw, color=color)


def icon_plus(color=MUTED):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawLine(s//2, s//4, s//2, s*3//4)
        p.drawLine(s//4, s//2, s*3//4, s//2)
    return _paint_icon(draw, color=color)


def icon_download(color=MUTED):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawRect(3, s-6, s-6, 3)
        p.drawLine(s//2, 3, s//2, s-6)
        p.drawLine(s//4, s//2 - 3, s//2, s-6)
        p.drawLine(s*3//4, s//2 - 3, s//2, s-6)
    return _paint_icon(draw, color=color)


def icon_filter(color=MUTED):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawLine(3, 4, s-3, 4)
        p.drawLine(s//4 + 2, 4, s//4 + 2, s-4)
        p.drawLine(s//2, 4, s//2, s-4)
        p.drawLine(s*3//4 - 2, 4, s*3//4 - 2, s-4)
    return _paint_icon(draw, color=color)


def icon_samples(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(s//2 - 3, 2, 6, s-4, 3, 3)
        p.drawEllipse(s//2 - 3, 2, 6, 6)
        p.drawLine(s//4 + 2, s//2, s*3//4 - 2, s//2)
        p.drawLine(s//4 + 2, s//2, s//4 + 2, s-4)
        p.drawLine(s*3//4 - 2, s//2, s*3//4 - 2, s-4)
    return _paint_icon(draw, color=color)


def icon_statistics(color=PRIMARY):
    def draw(p, s):
        p.setBrush(Qt.NoBrush)
        p.drawLine(3, s-4, s-3, s-4)
        p.drawLine(s//4, s-4, s//4, s//3)
        p.drawLine(s//2, s-4, s//2, s//4)
        p.drawLine(s*3//4, s-4, s*3//4, s//5)
        p.drawLine(s//4, s//3, s//2, s//4)
        p.drawLine(s//2, s//4, s*3//4, s//5)
    return _paint_icon(draw, color=color)
