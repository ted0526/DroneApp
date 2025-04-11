# DroneApp

A telemetry and testing suite for evaluating ESCs using a Teensy microcontroller and a Raspberry Pi-based GUI.

## 📁 Project Structure

- `Teensy Code/`  
  Contains all Arduino/Teensy sketches used for controlling ESCs, reading telemetry, and communicating with the Raspberry Pi.

- `piCode/`  
  The PyQt6-based GUI for displaying live telemetry, sending throttle commands, and running automated tests.

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

> If you haven’t generated a `requirements.txt` yet, I can help with that too!

## 📷 Preview

(Include screenshots of the GUI or test results here later)

## 📜 License

This project is private and currently not under an open-source license.

---

Let me know if you'd like to:
- add badges (e.g. Python version, build status)
- make a project logo/banner
- auto-generate docs for your classes (e.g., with Sphinx)

Would you like me to save this and push it as a commit?
