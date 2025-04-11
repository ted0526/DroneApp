#include <Arduino.h>
#define UART_PORT Serial1
#define BAUD_RATE 115200

void setup() {
  Serial.begin(115200);     // USB serial to console
  UART_PORT.begin(BAUD_RATE); // ESC UART input
  Serial.println("[UART Debug] Listening for telemetry bytes on Serial1");
}

void loop() {
  while (UART_PORT.available()) {
    uint8_t b = UART_PORT.read();
    Serial.print("0x");
    if (b < 0x10) Serial.print("0"); // zero-padding
    Serial.print(b, HEX);
    Serial.print(" ");
  }
  delay(10);
}
