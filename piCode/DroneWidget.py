from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QRect
from ESCWidget import ESCWidget

class DroneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.esc_widgets = [
            ESCWidget(name="GAN 1"),
            ESCWidget(name="SIC 2"),
            ESCWidget(name="GAN 2"),
            ESCWidget(name="SIC 2"),
        ]

        for esc in self.esc_widgets:
            esc.setParent(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        w = self.width()
        h = self.height()
        margin = 20

        esc_size = min((w - 3 * margin) // 2, (h - 3 * margin) // 2)

        self.esc_widgets[0].setGeometry(QRect(margin, margin, esc_size, esc_size))  # Top-left
        self.esc_widgets[1].setGeometry(QRect(w - esc_size - margin, margin, esc_size, esc_size))  # Top-right
        self.esc_widgets[2].setGeometry(QRect(margin, h - esc_size - margin, esc_size, esc_size))  # Bottom-left
        self.esc_widgets[3].setGeometry(QRect(w - esc_size - margin, h - esc_size - margin, esc_size, esc_size))  # Bottom-right

    def updateDrone(self, esc_data):
        """
        esc_data should be a dict like:
        {
            "GAN1": [voltage, current, temp1, temp2, rpm],
            "SIC1": [...],
            "GAN2": [...],
            "SIC2": [...]
        }
        """

        # Update ESC1 ← GAN1, ESC2 ← SIC1, ESC3 ← GAN2, ESC4 ← SIC2
        esc_order = ["GAN1", "SIC1", "GAN2", "SIC2"]

        for i, esc in enumerate(self.esc_widgets):
            esc_name = esc_order[i]
            if esc_name in esc_data:
                voltage, current, temp1, temp2, rpm = esc_data[esc_name]
                esc.update_data(temp1, temp2, voltage, current, rpm)
