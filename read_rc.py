import serial
import time

# === CONFIG ===
PORT = "COM4"  # Replace with your Teensy serial port or correct COM port
BAUD = 115200

# === MSP Command IDs ===
MSP_RC = 105  # Command ID for RC channels (throttle, roll, pitch, yaw, aux channels)

# === MSP Utilities ===
def build_msp_request(msp_id):
    return b"$M<" + bytes([0, msp_id, 0 ^ msp_id])

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
def parse_rc(payload):
    throttle = int.from_bytes(payload[0:2], 'little')
    roll = int.from_bytes(payload[2:4], 'little')
    pitch = int.from_bytes(payload[4:6], 'little')
    yaw = int.from_bytes(payload[6:8], 'little')
    aux1 = int.from_bytes(payload[8:10], 'little')
    aux2 = int.from_bytes(payload[10:12], 'little')
    aux3 = int.from_bytes(payload[12:14], 'little')
    aux4 = int.from_bytes(payload[14:16], 'little')
    return throttle, roll, pitch, yaw, aux1, aux2, aux3, aux4

# === Main Loop ===
with serial.Serial(PORT, BAUD, timeout=0.5) as ser:
    print("🔄 Reading RC channel telemetry (throttle, pitch, yaw, roll, aux channels)...")
    
    try:
        while True:
            # === MSP_RC ===
            ser.write(build_msp_request(MSP_RC))
            wait_for_response(ser)
            cmd, payload, checksum = get_payload(ser)
            throttle, roll, pitch, yaw, aux1, aux2, aux3, aux4 = parse_rc(payload)

            # Display RC telemetry values (throttle, roll, pitch, yaw, aux channels)
            print(f"\n🚦 Throttle: {throttle} (Raw value)")
            print(f"🌀 Roll: {roll}, Pitch: {pitch}, Yaw: {yaw}")
            print(f"🔲 Aux Channels: {aux1}, {aux2}, {aux3}, {aux4}")

            time.sleep(1)  # Wait before sending next command

    except KeyboardInterrupt:
        print("\n⛔ Stopped RC telemetry stream.")
