#include <ADC.h>

// --- ADC Setup ---
ADC adc;
const float VREF = 3300.0; // mV

// 16 analog sensor pins (A0–A9, A12–A17), split evenly across ADC0/ADC1
const int sensorPins[16] = {14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 26, 27, 38, 39, 40, 41};
float temps[16];

// --- MSP Serial Ports ---
#define FC1 Serial1
#define FC2 Serial2

// --- MSP Telemetry Values (placeholders for now) ---
float fc1_voltage = 0, fc1_current = 0, fc1_rssi = 0;
float fc2_voltage = 0, fc2_current = 0, fc2_rssi = 0;

// --- Command State ---
int command_throttle = 0;
int command_duration = 0;
bool command_ready = false;

// --- Timing ---
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 500; // 0.5 seconds

void setup() {
  Serial.begin(115200);
  FC1.begin(115200);
  FC2.begin(115200);

  // ADC0 config
  adc.adc0->setResolution(16);
  adc.adc0->setAveraging(16);
  adc.adc0->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
  adc.adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::HIGH_SPEED);

  // ADC1 config
  adc.adc1->setResolution(16);
  adc.adc1->setAveraging(16);
  adc.adc1->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
  adc.adc1->setSamplingSpeed(ADC_SAMPLING_SPEED::HIGH_SPEED);

  Serial.println("Teensy Telemetry Hub (with custom temp sensor logic) Ready.");
}

void loop() {
  checkPiCommand(); // Look for commands from Pi

  if (millis() - lastUpdate >= updateInterval) {
    lastUpdate = millis();

    readTemps();
    requestMSPData(FC1, fc1_voltage, fc1_current, fc1_rssi);
    requestMSPData(FC2, fc2_voltage, fc2_current, fc2_rssi);

    streamTelemetry();
  }
}

// ------------------------------------------
// TEMP SENSOR LOGIC
// ------------------------------------------
void readTemps() {
  for (int i = 0; i < 16; i++) {
    int raw;
    if (i % 2 == 0) {
      raw = adc.analogRead(sensorPins[i], ADC_0);
    } else {
      raw = adc.analogRead(sensorPins[i], ADC_1);
    }

    float voltage = raw * VREF / adc.adc0->getMaxValue();
    temps[i] = celsiusToFahrenheit(calculateTemperature(voltage));
  }
}

float calculateTemperature(float V_TEMP) {
  // Custom nonlinear equation
  float a = 8.194;
  float b = 0.00262;
  float c = 1324;
  float d = 30;

  float temp = a - sqrt(pow(-a, 2) + 4 * b * (c - V_TEMP));
  temp /= (2 * -b);
  temp += d;

  return temp;
}

int celsiusToFahrenheit(int tempC) {
  return (tempC * 9) / 5 + 32;
}

// ------------------------------------------
// MSP STUB (Mock values for now)
// ------------------------------------------
void requestMSPData(HardwareSerial &fc, float &voltage, float &current, float &rssi) {
  // TODO: Replace with actual MSP reads
  voltage = 15.0 + random(-50, 50) / 100.0;
  current = 3.0 + random(-10, 10) / 100.0;
  rssi    = 90 + random(-3, 3);
}

// ------------------------------------------
// TELEMETRY OUTPUT
// ------------------------------------------
void streamTelemetry() {
  Serial.print("T:[");
  for (int i = 0; i < 16; i++) {
    Serial.print(temps[i], 1);
    if (i < 15) Serial.print(",");
  }
  Serial.print("], FC1:[v=");
  Serial.print(fc1_voltage, 2);
  Serial.print("V, a=");
  Serial.print(fc1_current, 2);
  Serial.print("A, rssi=");
  Serial.print(fc1_rssi, 0);
  Serial.print("], FC2:[v=");
  Serial.print(fc2_voltage, 2);
  Serial.print("V, a=");
  Serial.print(fc2_current, 2);
  Serial.print("A, rssi=");
  Serial.print(fc2_rssi, 0);
  Serial.println("]");
}

// ------------------------------------------
// PI COMMAND PARSER
// ------------------------------------------
void checkPiCommand() {
  static String inputLine = "";

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      inputLine.trim();

      if (inputLine.startsWith("CMD:")) {
        inputLine.remove(0, 4); // Remove "CMD:"
        parseCommand(inputLine);
        command_ready = true;
      }

      inputLine = ""; // Clear buffer
    } else {
      inputLine += c;
    }
  }
}

void parseCommand(const String &cmd) {
  command_throttle = 0;
  command_duration = 0;

  int sep1 = cmd.indexOf(';');
  String part1 = cmd.substring(0, sep1);
  String part2 = cmd.substring(sep1 + 1);

  if (part1.startsWith("THROTTLE=")) {
    command_throttle = part1.substring(9).toInt();
  }

  if (part2.startsWith("DURATION=")) {
    command_duration = part2.substring(9).toInt();
  }

  Serial.print("[CMD RECEIVED] THROTTLE=");
  Serial.print(command_throttle);
  Serial.print("% for ");
  Serial.print(command_duration);
  Serial.println(" seconds");
}
