import os
import json
import csv
import serial
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QSpinBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import serial.tools.list_ports

class TestRunnerTab(QWidget):
    def __init__(self, baudrate=115200):
        super().__init__()

        self.baudrate = baudrate
        self.serial_connection = None
        self.logging = False
        self.log_data = []
        self.test_active = False
        self.test_started = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Serial port selection
        port_row = QHBoxLayout()
        self.port_selector = QComboBox()
        self.refresh_port_btn = QPushButton("Refresh 🔄")
        self.refresh_port_btn.setFixedWidth(100)
        self.refresh_port_btn.clicked.connect(self.refresh_ports)

        port_row.addWidget(self.port_selector)
        port_row.addWidget(self.refresh_port_btn)
        form.addRow("Serial Port:", port_row)


        # Test type selection
        self.test_type = QComboBox()
        self.test_type.addItems(["ramp", "step", "steady"])
        form.addRow("Test Type:", self.test_type)

        # Test duration input
        self.duration = QSpinBox()
        self.duration.setRange(1, 3600)
        self.duration.setSuffix(" sec")
        form.addRow("Duration:", self.duration)

        # Throttle low input
        self.throttle_low = QSpinBox()
        self.throttle_low.setRange(0, 100)
        form.addRow("Throttle Low:", self.throttle_low)

        # Throttle high input
        self.throttle_high = QSpinBox()
        self.throttle_high.setRange(0, 100)
        form.addRow("Throttle High:", self.throttle_high)

        self.throttle_low.setSuffix(" %")
        self.throttle_high.setSuffix(" %")

        # Log filename input
        self.filename = QLineEdit("test_001.csv")
        form.addRow("Log Filename:", self.filename)

        layout.addLayout(form)

        # Start button
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start Test")
        self.start_btn.clicked.connect(self.start_test)
        btn_row.addWidget(self.start_btn)
        layout.addLayout(btn_row)

        # Status and loader
        self.status = QLabel("Status: Idle")
        layout.addWidget(self.status)

        self.loader = QLabel("[ Running test... ]")
        self.loader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loader.setVisible(False)
        layout.addWidget(self.loader)

        self.setLayout(layout)

    def refresh_ports(self):
        self.port_selector.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_selector.addItem(f"{port.device} - {port.description}")

    def get_selected_port(self):
        entry = self.port_selector.currentText()
        return entry.split()[0] if entry else None

    def start_test(self):
        port = self.get_selected_port()
        if not port:
            QMessageBox.warning(self, "Warning", "Please select a serial port.")
            return

        try:
            self.serial_connection = serial.Serial(port, self.baudrate, timeout=1)
            self.send_test_config()
        except Exception as e:
            QMessageBox.critical(self, "Serial Error", str(e))
            self.status.setText("Status: Error")

    def send_test_config(self):
        config = {
            "type": self.test_type.currentText(),
            "duration": self.duration.value(),
            "throttle_low": self.throttle_low.value(),
            "throttle_high": self.throttle_high.value()
        }

        try:
            self.serial_connection.write(b"TEST_CONFIG:" + json.dumps(config).encode() + b"\n")
            self.status.setText("Status: Config sent. Waiting for ACK...")
            self.logging = True
            self.log_data = []
            self.loader.setVisible(True)
            threading.Thread(target=self.wait_for_ack_and_start_test, daemon=True).start()
        except Exception as e:
            QMessageBox.critical(self, "Serial Error", str(e))
            self.status.setText("Status: Error")

    def wait_for_ack_and_start_test(self):
        try:
            while True:
                line = self.serial_connection.readline().decode().strip()
                print("[ACK Wait]", line)

                if line == "CONFIG_RECEIVED":
                    self.status.setText("Status: Config acknowledged. Starting test.")
                    self.serial_connection.write(b"START_TEST\n")
                    self.logging = True
                    self.log_data = []
                    self.loader.setVisible(True)
                    threading.Thread(target=self.read_serial_loop, daemon=True).start()
                    return
                
                elif line: # Store any pre-ACK messages as log
                    if line.strip().lower() == "test started":
                        self.test_started = True
                        self.log_data.append("#Test started")
                    elif self.test_started:
                        if line[0].isdigit():
                            self.log_data.append(line)
                        else:
                            self.log_data.append('#' + line)
        except Exception as e:
            print("[ACK Error]", e)
            self.status.setText("Status: ACK Error")

    def read_serial_loop(self):
        while self.logging and self.serial_connection and self.serial_connection.is_open:
            try:
                line = self.serial_connection.readline().decode().strip()
                if not line:
                    continue

                print("[LOG]", line)

                if line == "TEST_ENDED":
                    self.logging = False
                    self.test_started = False
                    self.status.setText("Status: Test completed. Saving log...")
                    self.loader.setVisible(False)
                    self.save_log()
                    return

                if self.test_started:
                    if line[0].isdigit():
                        self.log_data.append(line)
                    else:
                        self.log_data.append('#' + line)
                elif line.strip().lower() == "test started":
                    self.test_started = True
                    self.log_data.append("#Test started")
            except Exception as e:
                print("[Read Error]", e)
                self.status.setText("Status: Read Error")
                self.loader.setVisible(False)
                return

    def save_log(self):
        filename = self.filename.text().strip()
        if not filename.endswith(".csv"):
            filename += ".csv"

        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        full_path = os.path.join(logs_dir, filename)

        header = [
            "Timestamp",
            "Voltage_GAN1", "Current_GAN1", "Temp1_GAN1", "Temp2_GAN1",
            "Voltage_SIC1", "Current_SIC1", "Temp1_SIC1", "Temp2_SIC1",
            "Voltage_GAN2", "Current_GAN2", "Temp1_GAN2", "Temp2_GAN2",
            "Voltage_SIC2", "Current_SIC2", "Temp1_SIC2", "Temp2_SIC2",
            "RPM_GAN1", "RPM_SIC1", "RPM_GAN2", "RPM_SIC2"
        ]

        try:
            with open(full_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for line in self.log_data:
                    writer.writerow(line.split(","))
            self.status.setText(f"Status: Log saved to {filename}")
        except Exception as e:
            self.status.setText("Status: Log save error")
            QMessageBox.critical(self, "File Error", str(e))
