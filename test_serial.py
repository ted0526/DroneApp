import serial
import time

# === CONFIG ===
PORT = "COM4"  # Replace with your FTDI COM port
BAUD = 115200

# === MSP Command IDs ===
MSP_ANALOG = 110
MSP_RAW_IMU = 102
MSP_STATUS_EX = 150

# === MSP Utilities ===
def build_msp_request(msp_id):
    return b"$M<" + bytes([0, msp_id, 0 ^ msp_id])

def calculate_checksum(cmd, payload):
    checksum = cmd
    for b in payload:
        checksum ^= b
    return checksum & 0xFF

def read_exact(ser, num_bytes):
    data = b""
    while len(data) < num_bytes:
        chunk = ser.read(num_bytes - len(data))
        if not chunk:
            raise TimeoutError("Serial read timeout")
        data += chunk
    return data

def wait_for_response(ser):
    while True:
        if ser.read(1) == b"$":
            if ser.read(1) == b"M" and ser.read(1) == b">":
                return

def get_payload(ser):
    payload_size = read_exact(ser, 1)[0]
    cmd = read_exact(ser, 1)[0]
    raw = read_exact(ser, payload_size + 1)
    payload = raw[:payload_size]
    checksum = raw[payload_size]
    return cmd, payload, checksum

# === Parsers ===
def parse_analog(payload):
    voltage = int.from_bytes(payload[0:2], 'little') / 10.0
    mAh = int.from_bytes(payload[2:4], 'little')
    amps = int.from_bytes(payload[4:6], 'little', signed=True) / 100.0
    rssi = payload[6]
    extra1 = payload[7]
    extra2 = payload[8]
    return voltage, amps, mAh, rssi, extra1, extra2

def parse_imu(payload):
    accel = tuple(int.from_bytes(payload[i:i+2], 'little', signed=True) for i in range(0, 6, 2))
    gyro  = tuple(int.from_bytes(payload[i:i+2], 'little', signed=True) for i in range(6, 12, 2))
    mag   = tuple(int.from_bytes(payload[i:i+2], 'little', signed=True) for i in range(12, 18, 2))
    return accel, gyro, mag

def parse_status_ex(payload):
    cycle_time = int.from_bytes(payload[0:2], 'little')
    errors = int.from_bytes(payload[2:4], 'little')
    cpu_load = payload[4]
    sensors = int.from_bytes(payload[5:9], 'little')
    return cycle_time, errors, cpu_load, sensors

# === Main Loop ===
with serial.Serial(PORT, BAUD, timeout=0.5) as ser:
    print("🔄 Streaming telemetry (no ESCs required)...")
    try:
        while True:
            # === MSP_ANALOG ===
            ser.write(build_msp_request(MSP_ANALOG))
            wait_for_response(ser)
            cmd, payload, checksum = get_payload(ser)
            voltage, amps, mAh, rssi, x1, x2 = parse_analog(payload)
            print(f"\n🔋 Battery: {voltage:.2f}V | ⚡ {amps:.2f}A | 📦 {mAh}mAh | 📶 RSSI: {rssi}")

            # === MSP_RAW_IMU ===
            ser.write(build_msp_request(MSP_RAW_IMU))
            wait_for_response(ser)
            cmd, payload, checksum = get_payload(ser)
            accel, gyro, mag = parse_imu(payload)
            print(f"🧭 IMU → Accel: {accel} | Gyro: {gyro} | Mag: {mag}")

            # === MSP_STATUS_EX ===
            ser.write(build_msp_request(MSP_STATUS_EX))
            wait_for_response(ser)
            cmd, payload, checksum = get_payload(ser)
            cycle_time, errors, cpu_load, sensors = parse_status_ex(payload)
            print(f"⚙️  System → Cycle: {cycle_time}µs | CPU: {cpu_load}% | Errors: {errors} | Sensors: 0x{sensors:08X}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⛔ Stopped telemetry stream.")
