from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QRectF

class ESCWidget(QWidget):
    def __init__(self, name="ESC", voltage=12.5, current=1.2, rpm=1500, temp1=30.0, temp2=35.0, parent=None):
        super().__init__(parent)
        self.name = name
        self.voltage = voltage
        self.current = current
        self.rpm = rpm
        self.temp1 = temp1
        self.temp2 = temp2
        self.rel_eff = self.calculate_efficiency()

    def calculate_efficiency(self):
        power = self.voltage * self.current
        return self.rpm / power if power != 0 else 0
    
    def update_data(self, temp1, temp2, voltage, current, rpm):
        self.temp1 = temp1
        self.temp2 = temp2
        self.voltage = voltage
        self.current = current
        self.rpm = rpm
        self.rel_eff = self.calculate_efficiency()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        size = min(rect.width(), rect.height())
        center_x = rect.center().x()
        center_y = rect.center().y()
        diameter = size - 10
        top_left_x = center_x - diameter / 2
        top_left_y = center_y - diameter / 2
        circle_rect = QRectF(top_left_x, top_left_y, diameter, diameter)

        theme = self.property("theme")
        if theme == "dark":
            fill_color = QColor("#1c1c1c")
            text_color = QColor("#f0f0f0")
            border_color = QColor("#a5acaf")
        else:
            fill_color = QColor("#004c93")  # GT Blue
            text_color = QColor("white")
            border_color = QColor("black")

        painter.setBrush(fill_color)
        painter.setPen(border_color)
        painter.drawEllipse(circle_rect)

        font = QFont()
        font.setPointSizeF(diameter / 15)
        painter.setFont(font)
        painter.setPen(text_color)

        lines = [
            self.name,
            f"{self.voltage:.1f}V / {self.current:.1f}A",
            f"{self.rpm} RPM",
            f"{self.temp1:.1f}°C / {self.temp2:.1f}°C",
            f"{self.rel_eff:.1f} RPM/W"
        ]

        fm = QFontMetrics(font)
        total_text_height = len(lines) * fm.height()
        y = center_y - total_text_height / 2 + fm.ascent()

        for line in lines:
            painter.drawText(QRectF(top_left_x, y - fm.ascent(), diameter, fm.height()),
                             Qt.AlignmentFlag.AlignCenter, line)
            y += fm.height()
