#define MSP_SET_RAW_RC 200
#define MSP_RC 105

uint16_t rcChannels[8] = {1000, 1500, 1500, 1500, 1500, 1500, 1500, 1500};
unsigned long lastSend = 0;
unsigned long lastRequest = 0;
const uint32_t mspBaud = 115200;

void setup() {
  Serial1.begin(mspBaud); // To flight controller
  Serial.begin(9600);     // To PC (Tera Term or Arduino Serial Monitor)
  while (!Serial) {}
  Serial.println("🚀 Teensy MSP RC Sender + Reader Started");
}

void loop() {
  unsigned long now = millis();

  // --- Send RC every 20ms (50Hz)
  if (now - lastSend >= 20) {
    sendMSPSetRawRC(rcChannels);
    Serial.print("Sent throttle: ");
    Serial.println(rcChannels[0]);
    lastSend = now;

    if (rcChannels[0] < 2000) {
      rcChannels[0] += 10;
    }
  }

  // --- Request MSP_RC every 100ms
  if (now - lastRequest >= 100) {
    requestMSPRC();
    lastRequest = now;
  }

  // --- Handle incoming MSP_RC response
  if (Serial1.available() >= 6) {
    if (Serial1.read() == '$' && Serial1.read() == 'M' && Serial1.read() == '>') {
      uint8_t payloadSize = Serial1.read();
      uint8_t cmd = Serial1.read();
      if (cmd == MSP_RC && payloadSize >= 16) {
        uint8_t payload[16];
        for (int i = 0; i < 16; i++) payload[i] = Serial1.read();
        uint8_t checksum = Serial1.read(); // discard or validate if you want

        uint16_t rcRead[8];
        for (int i = 0; i < 8; i++) {
          rcRead[i] = payload[i * 2] | (payload[i * 2 + 1] << 8);
        }

        Serial.print("🟢 FC RC Read - Throttle: ");
        Serial.print(rcRead[0]);
        Serial.print(" | Roll: ");
        Serial.print(rcRead[1]);
        Serial.print(" | Pitch: ");
        Serial.print(rcRead[2]);
        Serial.print(" | Yaw: ");
        Serial.println(rcRead[3]);
      }
    }
  }
}

void sendMSPSetRawRC(uint16_t rc[8]) {
  uint8_t payload[16];
  for (int i = 0; i < 8; i++) {
    payload[i * 2] = rc[i] & 0xFF;
    payload[i * 2 + 1] = rc[i] >> 8;
  }

  Serial1.write('$');
  Serial1.write('M');
  Serial1.write('<');
  Serial1.write((uint8_t)16);
  Serial1.write((uint8_t)MSP_SET_RAW_RC);

  uint8_t checksum = 16 ^ MSP_SET_RAW_RC;
  for (int i = 0; i < 16; i++) {
    Serial1.write(payload[i]);
    checksum ^= payload[i];
  }
  Serial1.write(checksum);
}

void requestMSPRC() {
  Serial1.write('$');
  Serial1.write('M');
  Serial1.write('<');
  Serial1.write((uint8_t)0);
  Serial1.write((uint8_t)MSP_RC);
  Serial1.write((uint8_t)(0 ^ MSP_RC));
}
