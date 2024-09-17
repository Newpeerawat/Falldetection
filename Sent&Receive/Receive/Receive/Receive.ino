/*#include <WiFi.h>
#include <esp_wifi.h>*/


// ตัวรับ RX ESP32
#include <esp_now.h>
#include <WiFi.h>

typedef struct struct_message {
    char a[32];
    int b;
    float c;
    bool d;
} struct_message;

struct_message myData;

// เมื่อรับข้อมูลมา ให้ทำในฟังก์ชั่นนี้
void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  memcpy(&myData, incomingData, sizeof(myData));
  Serial.print("Bytes received: ");
  Serial.println(len);
  Serial.print("Char: ");
  Serial.println(myData.a);
  Serial.print("Int: ");
  Serial.println(myData.b);
  Serial.print("Float: ");
  Serial.println(myData.c);
  Serial.print("Bool: ");
  Serial.println(myData.d);
  Serial.println();
}


/*void readMacAddress(){
  uint8_t baseMac[6];
  esp_err_t ret = esp_wifi_get_mac(WIFI_IF_STA, baseMac);
  if (ret == ESP_OK) {
    Serial.printf("%02x:%02x:%02x:%02x:%02x:%02x\n",
                  baseMac[0], baseMac[1], baseMac[2],
                  baseMac[3], baseMac[4], baseMac[5]); //{0xfc, 0xb4, 0x67, 0x72, 0x6d, 0x70};
  } else {
    Serial.println("Failed to read MAC address");
  }
}*/

void setup(){
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  WiFi.STA.begin();

  /*Serial.print("[DEFAULT] ESP32 Board MAC Address: "); //Read Address
  readMacAddress();*/

  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  // เมื่อรับข้อมูลมา ให้ทำในฟังก์ชั่น OnDataRecv ที่เราสร้างไว้
  esp_now_register_recv_cb(OnDataRecv);

}
 
void loop(){

}