void setup() {
  Serial.begin(115200);         // USB serial
  while (!Serial);

  Serial1.begin(115200);        // RX1 on pin 0
  Serial2.begin(115200);        // TX2 on pin 8

  Serial.println("UART loopback test starting...");
}

void loop() {
  // Send test string from TX2
  Serial2.println("Hello from TX2!");

  // Read from RX1 and print to USB serial
  while (Serial1.available()) {
    char c = Serial1.read();
    Serial.print(c);
  }

  delay(1000);  // 1 second delay between sends
}
