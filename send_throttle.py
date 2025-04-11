import serial
import time
import threading
import csv
from datetime import datetime

# === CONFIG ===
PORT = "COM4"   # Change this to your FTDI/CP2102 port
BAUD = 115200
MSP_SET_RAW_RC = 200
MSP_RC = 105
CSV_LOG_FILE = "ramp_results_cp2102.csv"

# === MSP Command Builders ===
def build_msp_set_raw_rc(throttle, roll, pitch, yaw, aux_channels=[1500]*8):
    header = b"$M<"
    payload = (
        throttle.to_bytes(2, 'little') +
        roll.to_bytes(2, 'little') +
        pitch.to_bytes(2, 'little') +
        yaw.to_bytes(2, 'little')
    )
    for aux in aux_channels:
        payload += aux.to_bytes(2, 'little')
    size = bytes([len(payload)])
    cmd = bytes([MSP_SET_RAW_RC])
    checksum = len(payload) ^ MSP_SET_RAW_RC
    for byte in payload:
        checksum ^= byte
    return header + size + cmd + payload + bytes([checksum])

def build_msp_request(msp_id):
    size = 0
    checksum = size ^ msp_id
    return b"$M<" + bytes([size, msp_id, checksum])

# === Serial Helpers ===
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
    return payload_size, cmd, payload, checksum

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

# === Background RC Sender ===
class RCSender(threading.Thread):
    def __init__(self, ser, throttle_ref, stop_event):
        super().__init__()
        self.ser = ser
        self.throttle_ref = throttle_ref
        self.stop_event = stop_event

    def run(self):
        roll = pitch = yaw = 1500
        aux = [1500] * 8
        while not self.stop_event.is_set():
            try:
                self.ser.write(build_msp_set_raw_rc(
                    self.throttle_ref[0], roll, pitch, yaw, aux))
                self.ser.flush()
                time.sleep(0.005)  # Short cooldown for CP2102
            except serial.SerialTimeoutException:
                print("⚠️ Serial write timeout — skipping cycle")
            time.sleep(0.07)  # ~14Hz for stability on CP2102

# === Ramp-Up Test ===
def ramp_up_with_logging(ser):
    throttle_ref = [1000]
    stop_event = threading.Event()
    sender = RCSender(ser, throttle_ref, stop_event)
    sender.start()

    roll = pitch = yaw = 1500
    aux = [1500] * 8
    step = 10
    delay_per_step = 0.5
    match_tolerance = 15

    print("🚀 Starting Throttle Ramp-Up Test (CP2102-Tuned)...")
    with open(CSV_LOG_FILE, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Throttle Sent", "Throttle Read", "Matched", "Response Time (s)"])

        for throttle in range(1000, 2001, step):
            throttle_ref[0] = throttle
            start_time = time.time()
            time.sleep(delay_per_step)  # Wait before reading

            try:
                ser.write(build_msp_request(MSP_RC))
                ser.flush()
                time.sleep(0.01)  # Give FC time to prepare response
                wait_for_response(ser)
                payload_size, cmd, payload, checksum = get_payload(ser)

                throttle_read, *_ = parse_rc(payload)

                if throttle_read == 0:
                    print(f"❌ Throttle {throttle}: FC ignored override")
                    writer.writerow([datetime.now(), throttle, 0, "NO", "0 (ignored)"])
                    continue

                matched = abs(throttle_read - throttle) <= match_tolerance
                response_time = time.time() - start_time
                status = "✅" if matched else "⚠️"

                print(f"{status} Throttle {throttle} → {throttle_read} in {response_time:.3f}s")
                writer.writerow([datetime.now(), throttle, throttle_read, "YES" if matched else "NO", f"{response_time:.3f}"])

            except Exception as e:
                print(f"⚠️ Error at throttle {throttle}: {e}")
                writer.writerow([datetime.now(), throttle, "ERR", "NO", f"Error: {e}"])

    stop_event.set()
    sender.join()
    ser.write(build_msp_set_raw_rc(1000, 1500, 1500, 1500, [1500] * 8))
    ser.flush()
    print("\n✅ Ramp test complete. CSV saved as:", CSV_LOG_FILE)

# === Run It ===
if __name__ == "__main__":
    try:
        with serial.Serial(PORT, BAUD, timeout=0.5, write_timeout=1.0) as ser:
            ramp_up_with_logging(ser)
    except KeyboardInterrupt:
        print("\n⛔ Interrupted.")
