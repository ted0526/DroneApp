#include <Arduino.h>
#include <ADC.h>
#include <ArduinoJson.h>

#define ESC_COUNT 4
#define VREF 3300
#define MUX_S0 20
#define MUX_S1 19
#define MUX_S2 18
#define MUX_Z_INPUT A0
#define BAUD_RATE 115200
#define THROTTLE_PIN 2
#define TELEMETRY_PACKET_SIZE 10

ADC adc;

bool is_test_running = false;
bool live_telemetry_active = false;
bool manual_throttle_override = false;

unsigned long test_start_time = 0;
unsigned long test_duration = 0;
unsigned long test_end_time = 0;
unsigned long last_telem_time = 0;
int throttle_value = 0;

String test_type = "";
int throttle_low = 0, throttle_high = 0;

struct EscTelemetry {
  uint16_t voltage = 0;
  uint16_t current = 0;
  uint16_t erpm = 0;
  uint8_t temperature = 0;
  bool valid = false;
};

EscTelemetry esc_data[ESC_COUNT];

HardwareSerial* esc_serials[ESC_COUNT] = { &Serial1, &Serial2, &Serial3, &Serial4 };
uint8_t esc_buffers[ESC_COUNT][TELEMETRY_PACKET_SIZE];

uint8_t update_crc8(uint8_t data, uint8_t crc) {
  crc ^= data;
  for (int i = 0; i < 8; ++i) {
    if (crc & 0x80) crc = (crc << 1) ^ 0x07;
    else crc <<= 1;
    crc &= 0xFF;
  }
  return crc;
}

uint8_t get_crc8(uint8_t* data, size_t len) {
  uint8_t crc = 0;
  for (size_t i = 0; i < len; ++i)
    crc = update_crc8(data[i], crc);
  return crc;
}

void read_uart_telemetry() {
  for (uint8_t i = 0; i < ESC_COUNT; i++) {
    if (esc_serials[i]->available() >= TELEMETRY_PACKET_SIZE) {
      esc_serials[i]->readBytes(esc_buffers[i], TELEMETRY_PACKET_SIZE);
      uint8_t* buf = esc_buffers[i];
      uint8_t crc = get_crc8(buf, 9);
      if (crc == buf[9]) {
        esc_data[i].temperature = buf[0];
        esc_data[i].voltage = ((buf[1] << 8) | buf[2]) * 10;
        esc_data[i].current = ((buf[3] << 8) | buf[4]) * 10;
        esc_data[i].erpm = ((buf[7] << 8) | buf[8]) * 10;
        esc_data[i].valid = true;
      } else {
        esc_data[i].valid = false;
      }
    }
  }
}

void selectMuxChannel(uint8_t channel) {
  digitalWrite(MUX_S0, (channel & 0x01) ? HIGH : LOW);
  digitalWrite(MUX_S1, (channel & 0x02) ? HIGH : LOW);
  digitalWrite(MUX_S2, (channel & 0x04) ? HIGH : LOW);
}

float calculateTemperature(float V_TEMP) {
  const float a = 8.194;
  const float b = 0.00262;
  const float c = 1324;
  const float d = 30;

  float temp = a - sqrt(pow(-a, 2) + 4 * b * (c - V_TEMP));
  temp /= (2 * -b);
  temp += d;
  return temp;
}

float readTemperatureFromMux(uint8_t muxChannel) {
  selectMuxChannel(muxChannel);
  delayMicroseconds(100);
  adc.adc1->analogRead(MUX_Z_INPUT);
  delayMicroseconds(100);
  uint16_t raw = adc.adc1->analogRead(MUX_Z_INPUT);
  float voltage = raw * (float)VREF / adc.adc1->getMaxValue();
  if (voltage < 100.0 || voltage > 1500.0) return NAN;
  return calculateTemperature(voltage);
}

void handle_test_config(const String& json_str) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, json_str);
  if (error) {
    Serial.println("Error parsing JSON");
    return;
  }
  test_type = doc["type"].as<String>();
  test_duration = doc["duration"];
  throttle_low = doc["throttle_low"];
  throttle_high = doc["throttle_high"];
  Serial.println("CONFIG_RECEIVED");
  if (test_type == "steady") throttle_value = throttle_low;
}

const uint8_t TEMP_MUX[ESC_COUNT][2] = {
  {6, 7}, // ESC1 - Top Left (GAN1)
  {4, 5}, // ESC2 - Bottom Left (SIC1)
  {2, 3}, // ESC3 - Bottom Right (GAN2)
  {0, 1}  // ESC4 - Top Right (SIC2)
};

void send_telemetry() {
  unsigned long timestamp = is_test_running ? millis() - test_start_time : millis();
  String telemetry = String(timestamp);

  for (uint8_t esc = 0; esc < ESC_COUNT; esc++) {
    float temp1 = readTemperatureFromMux(TEMP_MUX[esc][0]);
    float temp2 = readTemperatureFromMux(TEMP_MUX[esc][1]);
    float voltage = esc_data[esc].valid ? esc_data[esc].voltage / 1000.0 : 0.0;
    float current = esc_data[esc].valid ? esc_data[esc].current / 1000.0 : 0.0;
    telemetry += "," + String(voltage, 3) + "," + String(current, 3)
              + "," + String(temp1, 2) + "," + String(temp2, 2);
  }

  for (uint8_t esc = 0; esc < ESC_COUNT; esc++) {
    telemetry += "," + String(esc_data[esc].valid ? esc_data[esc].erpm : 0);
  }

  Serial.println(telemetry);
}

void setup() {
  Serial.begin(BAUD_RATE);
  for (uint8_t i = 0; i < ESC_COUNT; i++) esc_serials[i]->begin(115200);
  pinMode(MUX_S0, OUTPUT);
  pinMode(MUX_S1, OUTPUT);
  pinMode(MUX_S2, OUTPUT);
  pinMode(MUX_Z_INPUT, INPUT);
  pinMode(THROTTLE_PIN, OUTPUT);
  analogWriteFrequency(THROTTLE_PIN, 50);
  adc.adc1->setResolution(16);
  adc.adc1->setAveraging(32);
  adc.adc1->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
  adc.adc1->setSamplingSpeed(ADC_SAMPLING_SPEED::LOW_SPEED);
  Serial.println("Timestamp,"
    "Voltage_GAN1,Current_GAN1,Temp1_GAN1,Temp2_GAN1,"
    "Voltage_SIC1,Current_SIC1,Temp1_SIC1,Temp2_SIC1,"
    "Voltage_GAN2,Current_GAN2,Temp1_GAN2,Temp2_GAN2,"
    "Voltage_SIC2,Current_SIC2,Temp1_SIC2,Temp2_SIC2,"
    "RPM_GAN1,RPM_SIC1,RPM_GAN2,RPM_SIC2");
}

void loop() {
  while (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "START_LIVE") {
      live_telemetry_active = true;
      Serial.println("Live telemetry started.");
    }
    else if (cmd == "END_LIVE") {
      live_telemetry_active = false;
      throttle_value = 0;
      Serial.println("Live telemetry stopped. Throttle set to 0.");
    }
    else if (cmd.startsWith("THROTTLE:")) {
      throttle_value = cmd.substring(9).toInt();
      manual_throttle_override = true;
      Serial.print("Manual throttle override: ");
      Serial.println(throttle_value);
    }
    else if (cmd.startsWith("TEST_CONFIG:")) {
      handle_test_config(cmd.substring(12));
    }
    else if (cmd == "START_TEST") {
      is_test_running = true;
      manual_throttle_override = false;
      live_telemetry_active = true;
      test_start_time = millis();
      test_end_time = test_start_time + test_duration * 1000;
      Serial.println("Test started");
    }
    else if (cmd == "STOP_TEST") {
      is_test_running = false;
      throttle_value = 0;
      Serial.println("Test stopped, Throttle set to 0");
    }
  }

  unsigned long now = millis();
  if (is_test_running) {
    if (now >= test_end_time) {
      is_test_running = false;
      throttle_value = 0;
      Serial.println("TEST_ENDED");
    } else {
      if (test_type == "steady") throttle_value = throttle_low;
      else if (test_type == "ramp") throttle_value = constrain(map(now - test_start_time, 0, test_duration * 1000, throttle_low, throttle_high), throttle_low, throttle_high);
      else if (test_type == "step") throttle_value = (now / 1000) % 2 == 0 ? throttle_low : throttle_high;
    }
  }

  int pulse_us = map(throttle_value, 0, 100, 1000, 2000);
  int pwm_duty = map(pulse_us, 0, 20000, 0, 255);
  analogWrite(THROTTLE_PIN, pwm_duty);

  read_uart_telemetry();

  if (live_telemetry_active && now - last_telem_time >= 30 ) { //poll speed
    send_telemetry();
    last_telem_time = now;
  }
}
