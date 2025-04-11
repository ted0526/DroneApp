import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from PlotWidget import TestResultPlot  # Import the plotting module

# Initialize PyQt Application
app = QApplication(sys.argv)

# Load test data
csv_filename = "logs/gui_test.csv"
df = pd.read_csv(csv_filename)
df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
df["Temp_GAN"] = df[["Temp1_GAN", "Temp2_GAN", "Temp3_GAN", "Temp4_GAN"]].mean(axis=1)
df["Temp_Control"] = df[["Temp1_Control", "Temp2_Control", "Temp3_Control", "Temp4_Control"]].mean(axis=1)

# Create PlotWidget instance for comparison

comparison_plot = TestResultPlot("ESC Comparison")
comparison_plot.plot_data(df, "Timestamp")

# Show the plot
app.processEvents()  # Ensure Qt updates the window
comparison_plot.show()
sys.exit(app.exec())