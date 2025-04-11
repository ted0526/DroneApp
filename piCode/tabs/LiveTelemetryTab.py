import os
import serial
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QSlider, QHBoxLayout, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import serial.tools.list_ports
from DroneWidget import DroneWidget

class LiveTelemetryTab(QWidget):
    esc_update_signal = pyqtSignal(dict)

    def __init__(self, baudrate=115200):
        super().__init__()

        self.baudrate = baudrate
        self.serial_connection = None
        self.reading = False

        main_layout = QVBoxLayout(self)

        # Serial port selection and connect/disconnect
        port_row = QHBoxLayout()
        self.port_selector = QComboBox()
        self.refresh_ports()
        port_row.addWidget(QLabel("Serial Port:"))
        port_row.addWidget(self.port_selector)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        port_row.addWidget(self.connect_btn)
        main_layout.addLayout(port_row)

        # Drone widget (4 ESCs)
        self.drone_widget = DroneWidget()
        self.drone_widget.setMinimumSize(QSize(800, 800))
        self.drone_widget.setMaximumSize(QSize(1600, 1600))
        self.drone_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.drone_widget, alignment=Qt.AlignmentFlag.AlignCenter, stretch=1)

        # Throttle slider
        throttle_row = QHBoxLayout()
        self.throttle_value_label = QLabel("Throttle: 0%")
        throttle_row.addWidget(self.throttle_value_label)

        self.throttle_slider = QSlider(Qt.Orientation.Horizontal)
        self.throttle_slider.setRange(0, 100)
        self.throttle_slider.setValue(0)
        self.throttle_slider.setTickInterval(5)
        self.throttle_slider.valueChanged.connect(self.send_throttle)
        throttle_row.addWidget(self.throttle_slider)

        main_layout.addLayout(throttle_row)

        # Status label
        self.status = QLabel("Status: Disconnected")
        main_layout.addWidget(self.status)

        self.setLayout(main_layout)

        # Connect telemetry signal to widget
        self.esc_update_signal.connect(self.drone_widget.updateDrone)

    def refresh_ports(self):
        self.port_selector.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_selector.addItem(f"{port.device} - {port.description}")

    def get_selected_port(self):
        entry = self.port_selector.currentText()
        return entry.split()[0] if entry else None

    def toggle_connection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.get_selected_port()
        if not port:
            QMessageBox.warning(self, "Warning", "Please select a serial port.")
            return

        try:
            self.serial_connection = serial.Serial(port, self.baudrate, timeout=1)
            self.serial_connection.write(b"START_LIVE\n")
            self.status.setText("Status: Connected (Live Telemetry)")
            self.connect_btn.setText("Disconnect")
            self.reading = True
            threading.Thread(target=self.read_serial_loop, daemon=True).start()
        except Exception as e:
            QMessageBox.critical(self, "Serial Error", str(e))
            self.status.setText("Status: Error")

    def disconnect_serial(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(b"END_LIVE\n")
                self.serial_connection.close()
            self.status.setText("Status: Disconnected")
            self.connect_btn.setText("Connect")
            self.reading = False
        except Exception as e:
            QMessageBox.critical(self, "Serial Error", str(e))

    def send_throttle(self, value):
        self.throttle_value_label.setText(f"Throttle: {value}%")
        pulse_value = value
        if self.serial_connection and self.serial_connection.is_open:
            cmd = f"THROTTLE:{value}\n".encode()
            try:
                self.serial_connection.write(cmd)
            except Exception as e:
                print("Throttle send failed:", e)

    def read_serial_loop(self):
        while self.reading and self.serial_connection and self.serial_connection.is_open:
            try:
                line = self.serial_connection.readline().decode().strip()
                if not line:
                    continue

                print("[LOG]", line)

                parts = [p if p.strip() != '' else '0.0' for p in line.split(',')]
                if len(parts) != 21:
                    print(f"[SKIP] Bad line: {line}")
                    continue

                esc_data = {
                    "GAN1": [float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]), float(parts[17])],
                    "SIC1": [float(parts[5]), float(parts[6]), float(parts[7]), float(parts[8]), float(parts[18])],
                    "GAN2": [float(parts[9]), float(parts[10]), float(parts[11]), float(parts[12]), float(parts[19])],
                    "SIC2": [float(parts[13]), float(parts[14]), float(parts[15]), float(parts[16]), float(parts[20])],
                }

                self.esc_update_signal.emit(esc_data)

            except Exception as e:
                print("[Telemetry Read Error]", e)
                self.status.setText("Status: Read Error")
                self.disconnect_serial()
                return
