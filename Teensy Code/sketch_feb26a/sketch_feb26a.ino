#include <Arduino.h>
#include <ADC.h>

const uint8_t MUX_S0 = 33;
const uint8_t MUX_S1 = 34;
const uint8_t MUX_S2 = 35;
const uint8_t MUX_Z_INPUT = A13;   // MUX Z → A13

#define VREF 3300
#define ESC_COUNT 4

ADC adc;

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
  delayMicroseconds(10);  // let mux settle

  uint16_t raw = adc.adc1->analogRead(MUX_Z_INPUT);
  float voltage = raw * (float)VREF / adc.adc1->getMaxValue();
  return calculateTemperature(voltage);
}

void setup() {
  Serial.begin(115200);

  pinMode(MUX_S0, OUTPUT);
  pinMode(MUX_S1, OUTPUT);
  pinMode(MUX_S2, OUTPUT);
  pinMode(MUX_Z_INPUT, INPUT);

  adc.adc1->setResolution(16);
  adc.adc1->setAveraging(16);
  adc.adc1->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
  adc.adc1->setSamplingSpeed(ADC_SAMPLING_SPEED::HIGH_SPEED);

  // CSV Header
  Serial.println("Timestamp,"
    "Voltage_GAN1,Current_GAN1,Temp1_GAN1,Temp2_GAN1,"
    "Voltage_SIC1,Current_SIC1,Temp1_SIC1,Temp2_SIC1,"
    "Voltage_GAN2,Current_GAN2,Temp1_GAN2,Temp2_GAN2,"
    "Voltage_SIC2,Current_SIC2,Temp1_SIC2,Temp2_SIC2");
}

void loop() {
  unsigned long now = millis();
  Serial.print(now);

  for (uint8_t esc = 0; esc < ESC_COUNT; esc++) {
    // Mux channels: each ESC gets 2 temp sensors
    uint8_t muxA = esc * 2;
    uint8_t muxB = esc * 2 + 1;

    float temp1 = readTemperatureFromMux(muxA);
    float temp2 = readTemperatureFromMux(muxB);

    // Simulate voltage/current for now
    float voltage = 11.0 + random(-100, 100) / 1000.0;
    float current = 4.5 + random(-100, 100) / 1000.0;

    // Append values to the CSV line
    Serial.print(",");
    Serial.print(voltage, 3);
    Serial.print(",");
    Serial.print(current, 3);
    Serial.print(",");
    Serial.print(temp1, 2);
    Serial.print(",");
    Serial.print(temp2, 2);
  }

  Serial.println();
  delay(1000);  // Log once per second
}
