import serial
import time
from collections import Counter

PORT = "COM4"  # 🔧 Update to your FTDI COM port
BAUD = 115200  # ✅ Must match Betaflight UART1 config (from your setup)

VALID_CRSF_HEADERS = {0xC8, 0xEA, 0xEC, 0xEE}

def main():
    counter = Counter()
    print(f"[INFO] Listening on {PORT} at {BAUD} baud...")

    with serial.Serial(PORT, BAUD, timeout=0.01) as ser:
        start_time = time.time()
        last_report = start_time

        while True:
            now = time.time()

            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                counter.update(data)

                # Print hex dump of what we see
                print(" ".join(f"{b:02X}" for b in data))

                # Look for CRSF frame starts
                if any(b in VALID_CRSF_HEADERS for b in data):
                    print("🚀 Possible CRSF packet detected!")

            # Show summary every 5 seconds
            if now - last_report >= 5:
                print("\n📊 Byte Frequency Summary:")
                for byte, count in counter.most_common(10):
                    print(f"  0x{byte:02X} : {count} times")
                print("------------------------------------------------")
                last_report = now

if __name__ == "__main__":
    main()
