from PyQt6.QtWidgets import QApplication, QMainWindow
from DroneWidget import DroneWidget
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(DroneWidget())
        self.setWindowTitle("4 ESCs in a Square")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
