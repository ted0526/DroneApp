import serial
import time

CRSF_ADDRESSES = {0xC8, 0xEA, 0xEC, 0xEE}
BAUD_CANDIDATES = [57600, 115200, 416666, 420000]

PORT = "COM4"  # Change to your FTDI port
TIMEOUT_PER_BAUD = 3  # seconds per test

def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0xD5
            else:
                crc <<= 1
            crc &= 0xFF
    return crc

def test_baud(baud):
    print(f"\n[INFO] Testing baud rate: {baud}")
    try:
        with serial.Serial(PORT, baudrate=baud, timeout=0.1) as ser:
            start_time = time.time()
            while time.time() - start_time < TIMEOUT_PER_BAUD:
                if ser.in_waiting < 2:
                    continue

                addr = ser.read(1)[0]
                if addr not in CRSF_ADDRESSES:
                    continue

                length = ser.read(1)[0]
                if ser.in_waiting < length + 1:
                    continue

                payload = ser.read(length)
                crc = ser.read(1)[0]

                if crc8(payload) == crc:
                    print(f"[✓] Valid packet detected at {baud} baud (type: 0x{payload[0]:02X})")
                    return True
    except Exception as e:
        print(f"[ERROR] Failed at {baud} baud: {e}")
    return False

def main():
    for baud in BAUD_CANDIDATES:
        if test_baud(baud):
            print(f"\n🎯 [SUCCESS] CRSF telemetry confirmed at {baud} baud")
            return
    print("\n❌ No valid CRSF packets detected at tested baud rates.")

if __name__ == "__main__":
    main()
