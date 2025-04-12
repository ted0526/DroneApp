import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt
from TabWidget import TabWidget
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1920, 1000)

        self.setCentralWidget(TabWidget())
        self.setWindowTitle("ESC Test Suite")
        self.fullscreen = False

        # Add F12 toggle
        QShortcut(QKeySequence("F12"), self, self.toggle_fullscreen)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply stylesheet
    with open(resource_path("style.qss"), "r") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
