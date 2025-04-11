from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout
from tabs.LiveTelemetryTab import LiveTelemetryTab
from tabs.TestRunnerTab import TestRunnerTab
from tabs.DataVisualizerTab import DataVisualizerTab

class TabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESC Test Suite")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout(self)

        # Add theme toggle button above the tabs
        toggle_row = QHBoxLayout()
        self.theme_button = QPushButton("Toggle Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        toggle_row.addStretch()
        toggle_row.addWidget(self.theme_button)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(LiveTelemetryTab(), "Live Telemetry")
        self.tab_widget.addTab(TestRunnerTab(), "Live Test Runner")
        self.tab_widget.addTab(DataVisualizerTab(), "Data Visualizer")
        layout.addWidget(self.tab_widget)

        self.setLayout(layout)
        
    def toggle_theme(self):
        new_theme = "dark" if self.property("theme") != "dark" else ""
        self.setProperty("theme", new_theme)
        self.style().polish(self)

        if self.window():
            self.window().setProperty("theme", new_theme)
            self.window().style().polish(self.window())

        for widget in self.findChildren(QWidget):
            widget.setProperty("theme", new_theme)
            widget.style().polish(widget)
