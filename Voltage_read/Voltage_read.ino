#include <driver/adc.h>
#include <esp_adc_cal.h>

#define V_REF 1100 // ค่าอ้างอิงแรงดันไฟ (1100 mV)

void setup() {
  Serial.begin(115200);
  analogReadResolution(12); // ตั้งค่า ADC ความละเอียดเป็น 12 บิต
}

void loop() {
  int raw = analogRead(36); // อ่านค่า ADC จากพิน GPIO36 (ADC1_CHANNEL_0)
  float voltage = (raw / 4095.0) * V_REF;
  Serial.print("Voltage: ");
  Serial.print(voltage);
  Serial.println(" mV");

  delay(1000); // รอ 1 วินาทีก่อนอ่านค่าใหม่
}