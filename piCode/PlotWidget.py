import matplotlib
matplotlib.use("QtAgg")  # Force Matplotlib to use Qt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # Use Qt6 backend
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
import pandas as pd

class TestResultPlot(QWidget):
    def __init__(self, title):
        super().__init__()
        self.figure, self.axes = plt.subplots(2, 2, figsize=(10, 8), sharex=True)
        self.canvas = FigureCanvas(self.figure)
        
        # Layout for the plot
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        
        # Title Label
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMaximumHeight(20)
        layout.addWidget(label)
        
        self.setLayout(layout)

    def plot_data(self, df, x_col):
        """ Generates 4 separate plots in a 2x2 layout comparing GAN and Control """
        
        # Convert timestamps to elapsed time (seconds)
        df[x_col] = (df[x_col] - df[x_col].iloc[0]).dt.total_seconds()

        # Clear only the axes, not the figure
        for row in self.axes:
            for ax in row:
                ax.clear()
        
        plot_configs = [
            ("Avg Temp", "Temp_GAN", "Temp_Control", "red", "blue"),
            ("RPM", "RPM_GAN", "RPM_Control", "green", "orange"),
            ("Voltage", "Voltage_GAN", "Voltage_Control", "purple", "brown"),
            ("Current", "Current_GAN", "Current_Control", "pink", "black"),
        ]
        
        for ax, (title, gan_col, control_col, gan_color, control_color) in zip(self.axes.flatten(), plot_configs):
            # Skip if required columns are missing
            if gan_col not in df.columns or control_col not in df.columns:
                print(f"⚠️ Missing column: {gan_col} or {control_col}, skipping plot: {title}")
                continue
            
            ax.plot(df[x_col], df[gan_col], label=f"GAN {title}", color=gan_color)
            ax.plot(df[x_col], df[control_col], label=f"Control {title}", color=control_color, linestyle="dashed")
            ax.set_ylabel(title)
            ax.legend()
        
        self.axes[1, 0].set_xlabel("Time (seconds)")
        self.axes[1, 1].set_xlabel("Time (seconds)")
        self.figure.tight_layout()
        self.canvas.draw()
