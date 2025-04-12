import os
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QLabel, QGridLayout, QPushButton,
    QHBoxLayout, QScrollArea, QTableWidget, QTableWidgetItem, QSizePolicy
)

# Matplotlib setup
import matplotlib
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class DataVisualizerTab(QWidget):
    def __init__(self):
        super().__init__()

        # Scrollable layout setup
        outer_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.inner_layout = QVBoxLayout(scroll_widget)

        self.figures = []
        self.current_filename = ""

        # File selector + generate button
        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("Log File:"))

        # Wrap file selector + refresh in sublayout
        file_selector_row = QHBoxLayout()
        self.file_selector = QComboBox()
        self.refresh_file_btn = QPushButton("Refresh 🔄")
        self.refresh_file_btn.setFixedWidth(100) 
        self.refresh_file_btn.clicked.connect(self.refresh_file_list)
        file_selector_row.addWidget(self.file_selector)
        file_selector_row.addWidget(self.refresh_file_btn)

        file_row.addLayout(file_selector_row)

        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_from_selection)
        file_row.addWidget(self.generate_button)

        self.inner_layout.addLayout(file_row)

        # Grid for ESC plots and summary
        self.plot_grid = QGridLayout()
        self.inner_layout.addLayout(self.plot_grid)

        # Save button
        self.save_button = QPushButton("Save All Charts as PNG")
        self.save_button.clicked.connect(self.save_all_charts)
        self.save_button.setEnabled(False)
        self.inner_layout.addWidget(self.save_button)

        scroll_area.setWidget(scroll_widget)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

        self.refresh_file_list()

    def refresh_file_list(self):
        logs_path = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        files = [f for f in os.listdir(logs_path) if f.endswith(".csv")]
        self.file_selector.clear()
        self.file_selector.addItems(files)

    def generate_from_selection(self):
        filename = self.file_selector.currentText()
        if filename:
            self.current_filename = filename
            self.load_and_plot(filename)

    def load_and_plot(self, filename):
        path = os.path.join("logs", filename)
        try:
            df = pd.read_csv(path)
            df = df[pd.to_numeric(df["Timestamp"], errors="coerce").notna()].copy()
            df = df.apply(pd.to_numeric, errors='coerce')
        except Exception as e:
            print(f"Failed to read file: {e}")
            return

        while self.plot_grid.count():
            item = self.plot_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.figures.clear()

        timestamp = df["Timestamp"]
        esc_labels = ["GAN1", "SIC1", "GAN2", "SIC2"]
        fig_size = (6, 4)

        # 1. RPM Comparison
        rpm_fig, rpm_ax = plt.subplots(figsize=fig_size, tight_layout=True)
        for esc in esc_labels:
            col = f"RPM_{esc}"
            if col in df.columns:
                rpm_ax.plot(timestamp, df[col], label=esc)
        rpm_ax.set_title("RPM Comparison")
        rpm_ax.set_xlabel("Time")
        rpm_ax.set_ylabel("RPM")
        rpm_ax.legend()
        rpm_ax.grid(True)
        self.add_plot_to_grid("RPM", rpm_fig, 0, 0)

        # 2. Temperature Comparison
        temp_fig, temp_ax = plt.subplots(figsize=fig_size, tight_layout=True)
        for esc in esc_labels:
            t1 = df.get(f"Temp1_{esc}", pd.Series([0]*len(df)))
            t2 = df.get(f"Temp2_{esc}", pd.Series([0]*len(df)))
            avg_temp = (t1 + t2) / 2
            temp_ax.plot(timestamp, avg_temp, label=esc)
        temp_ax.set_title("Temperature Comparison")
        temp_ax.set_xlabel("Time")
        temp_ax.set_ylabel("°C")
        temp_ax.legend()
        temp_ax.grid(True)
        self.add_plot_to_grid("Temperature", temp_fig, 0, 1)

        # 3. Current Comparison
        current_fig, current_ax = plt.subplots(figsize=fig_size, tight_layout=True)
        for esc in esc_labels:
            col = f"Current_{esc}"
            if col in df.columns:
                current_ax.plot(timestamp, df[col], label=esc)
        current_ax.set_title("Current Comparison")
        current_ax.set_xlabel("Time")
        current_ax.set_ylabel("Amps")
        current_ax.legend()
        current_ax.grid(True)
        self.add_plot_to_grid("Current", current_fig, 1, 0)

        # 4. Voltage Comparison
        voltage_fig, voltage_ax = plt.subplots(figsize=fig_size, tight_layout=True)
        for esc in esc_labels:
            col = f"Voltage_{esc}"
            if col in df.columns:
                voltage_ax.plot(timestamp, df[col], label=esc)
        voltage_ax.set_title("Voltage Comparison")
        voltage_ax.set_xlabel("Time")
        voltage_ax.set_ylabel("Volts")
        voltage_ax.legend()
        voltage_ax.grid(True)
        self.add_plot_to_grid("Voltage", voltage_fig, 1, 1)

        self.save_button.setEnabled(True)

        # Relative Efficiency Comparison (eRPM / W)
        eff_fig, eff_ax = plt.subplots(figsize=fig_size, tight_layout=True)
        for esc in esc_labels:
            try:
                rpm = df[f"RPM_{esc}"]
                v = df[f"Voltage_{esc}"]
                c = df[f"Current_{esc}"]
                power = (v * c)
                power[power < 1e-3] = 1e-3
                eff = (rpm / power)
                eff_ax.plot(timestamp, eff, label=esc)
            except Exception as e:
                print(f"[Efficiency Plot Error] {esc}: {e}")

        eff_ax.set_title("Relative Efficiency (eRPM / Watt)")
        eff_ax.set_xlabel("Time")
        eff_ax.set_yscale("log")
        eff_ax.set_ylabel("eRPM / W (log scale)")
        eff_ax.legend()
        eff_ax.grid(True)
        self.add_plot_to_grid("Efficiency", eff_fig, 2, 0)

        # Summary Stats Table (Max / Avg only)
        summary_fig, summary_ax = plt.subplots(figsize=(8, 2.2))
        summary_ax.axis('off')  # No axis lines or ticks

        metrics = ["RelEff", "Volt", "Curr", "Temp"]
        rows = ["Max", "Avg"]
        esc_labels = ["GAN1", "SIC1", "GAN2", "SIC2"]

        # Build columns: e.g., RPM Max, RPM Avg, Voltage Max, Voltage Avg, ...
        col_labels = []
        for metric in metrics:
            col_labels.extend([f"{metric} Max", f"{metric} Avg"])

        # Gather values
        data_matrix = []

        for esc in esc_labels:
            try:
                rpm = df[f"RPM_{esc}"]
                v = df[f"Voltage_{esc}"]
                c = df[f"Current_{esc}"]
                t1 = df.get(f"Temp1_{esc}", pd.Series([0]*len(df)))
                t2 = df.get(f"Temp2_{esc}", pd.Series([0]*len(df)))
                # Compute relative efficiency
                power = v * c
                power[power < 1e-3] = 1e-3  # avoid divide by near-zero
                eff = rpm / power
                temp = (t1 + t2) / 2
                esc_row = []
                for signal in [eff, v, c, temp]:
                    esc_row.extend([
                        f"{signal.max():.2f}",
                        f"{signal.mean():.2f}"
                    ])
                data_matrix.append(esc_row)
            except Exception as e:
                print(f"[Summary Table Error] {esc}: {e}")
                data_matrix.append(["N/A"] * (len(metrics) * len(rows)))

        # Add table to figure
        table = summary_ax.table(
            cellText=data_matrix,
            rowLabels=esc_labels,
            colLabels=col_labels,
            loc='center',
            cellLoc='center'
        )

        table.scale(1.2, 1.3)
        summary_ax.set_title("ESC Summary Stats (Max / Avg)", fontweight='bold')
        self.add_plot_to_grid("SummaryTable", summary_fig, 2, 1)

            

    def add_plot_to_grid(self, label, fig, row, col):
        canvas = FigureCanvas(fig)
        self.plot_grid.addWidget(canvas, row, col)
        self.figures.append((label, fig))

    def save_all_charts(self):
        if not self.current_filename:
            return
        base_name = os.path.splitext(self.current_filename)[0]
        save_dir = os.path.join(os.getcwd(), "plots", base_name)
        os.makedirs(save_dir, exist_ok=True)
        for esc_name, fig in self.figures:
            filename = f"{esc_name}.png"
            path = os.path.join(save_dir, filename)
            fig.savefig(path)
            print(f"✅ Saved {path}")
