from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget


class ProgressRing(QWidget):
    def __init__(self):
        super().__init__()
        self.progress = 0.0
        self.value_text = "0"
        self.target_text = "/0"
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_progress(self, progress, value_text, target_text):
        self.progress = max(0.0, min(float(progress), 1.0))
        self.value_text = str(value_text)
        self.target_text = str(target_text)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(14, 14, self.width() - 28, self.height() - 28)

        bg_pen = QPen(QColor("#3e3e42"), 8)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        progress_pen = QPen(QColor("#22c55e"), 8)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, 90 * 16, -int(360 * self.progress * 16))

        painter.setPen(QColor("#d4d4d4"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.value_text)

        painter.setPen(QColor("#858585"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(0, self.height() / 2 + 24, self.width(), 24),
            Qt.AlignCenter,
            self.target_text,
        )