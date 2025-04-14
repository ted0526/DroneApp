# DroneApp

A telemetry and testing suite for evaluating ESCs using a Teensy microcontroller and a Raspberry Pi-based GUI.

## 📁 Project Structure

- `Teensy Code/`  
  Contains all Arduino/Teensy sketches used for controlling ESCs, reading telemetry, and communicating with the Raspberry Pi.
  Final_Build_49 is the final version of the firmware written for the Teensy 4.0.
  Final_Build is the original final version written for the Teensy 4.1.
  Other .ino files were simply dev versions and different test code.

  ### 📁 piCode/ — PyQt6 GUI

  This directory contains the full graphical interface used for live telemetry display, test configuration, and ESC control.

  | File / Folder       | Description |
  |---------------------|-------------|
  | main.py             | Entry point for launching the GUI |
  | tabs/               | Contains the tabbed interface views: Live Telemetry, Test Runner, and Data Visualizer |
  | ESCWidget.py        | Custom PyQt6 widget for rendering individual ESC data (voltage, current, temperature, RPM, and efficiency) |
  | DroneWidget.py      | Composite widget that arranges 4 ESCWidgets into a single drone overview display |

- `venv/`  
  Local virtual environment (ignored in `.gitignore`).

- `.gitignore`  
  Standard exclusions for Python, PyQt6, and PyInstaller builds.

## 🧪 Features

- Live telemetry visualization from 4 ESCs (voltage, current, RPM, temperature)
- Throttle control via GUI
- Configurable test execution (e.g., ramp tests)
- Data logging to CSV for post-analysis

## 🚀 Getting Started

1. **Clone the repo:**

    ```bash
    git clone https://github.com/ted0526/DroneApp.git
    cd DroneApp
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the GUI:**

    ```bash
    cd piCode
    python main.py
    ```

## 📷 Preview

(Include screenshots of the GUI or test results here later)

## 📜 License

This project is private and currently not under an open-source license.

---

