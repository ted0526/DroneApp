from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ESCWidget import ESCWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Creating ESCWidget instances
        esc1 = ESCWidget(name="ESC1", voltage=12.5, current=1.2, rpm=1500, temp1=35.0, temp2=40.0)
        esc2 = ESCWidget(name="ESC2", voltage=12.5, current=1.0, rpm=1600, temp1=36.0, temp2=41.0)

        layout.addWidget(esc1)
        layout.addWidget(esc2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setWindowTitle("ESC Widgets")

# Running the Application
app = QApplication([])
window = MainWindow()
window.show()
app.exec()
