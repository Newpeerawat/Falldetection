#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#include <TinyGPS++.h>

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

#include <HTTPClient.h>

/*#include <driver/adc.h>
#include <esp_adc_cal.h>
#define V_REF 1100 // ค่าอ้างอิงแรงดันไฟ (1100 mV)*/


/*const char* ssid = "ctpproducts 2G"; //ESP32 IP Address: 192.168.1.50
const char* password = "sena8011";*/

const char* ssid = "Newpeerawat"; //ESP32 IP Address: 192.168.42.102
const char* password = "New@3103"; //IP Address mobile: 10.36.14.71


//Gps Function
// สร้างวัตถุ TinyGPSPlus
TinyGPSPlus gps;

// กำหนดพินที่ใช้สำหรับการเชื่อมต่อ GPS กับ ESP32
// GPS Tx -> RX pin of ESP32 (e.g., GPIO 16)
// GPS Rx -> TX pin of ESP32 (e.g., GPIO 17)
HardwareSerial mygps(1); // ใช้ UART1
void sendGPS();
void sendToGoogleSheets(float lat, float lng);


//MPU Function
Adafruit_MPU6050 mpu;
void SetMPU6050();

//Count function
int count_fall=0;
int start_ESP32=0;

void setup()
{
  Serial.begin(115200);
  //analogReadResolution(12); // ตั้งค่า ADC ความละเอียดเป็น 12 บิต
  delay(10);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

   //Set up Gps
  // เริ่มต้น mygps สำหรับการติดต่อสื่อสารกับโมดูล GPS
  // โดยใช้พอร์ต 1 ของ ESP32 (TX2 = 17, RX2 = 16)
  mygps.begin(9600, SERIAL_8N1, 16, 17); // บิตต่อวินาที, รูปแบบข้อมูล, RX, TX

  //Set up MPU
  SetMPU6050();
}


void loop()
{  
  if(start_ESP32==0){ //Status is on
    sendToGoogleSheets(0.0,0.0);
    start_ESP32++;
  }  
      //Reading MPU sensor (ตอนนี้ใช้แค่ acceleration)
    sensors_event_t a, g, temp; //ตัวแปร acceleration,gyro,temp
    mpu.getEvent(&a, &g, &temp);

    if(count_fall!=0){ //ถ้าล้มแล้วsensorIMUหยุดจับไปแล้วยังคงต้องส่งตำแหน่งอยู่ไม่งั้นมันไม่ส่งตำแหน่ง
      Serial.println("Already Fall");
      /*for(int i=0; i<2; i++){
        sendGPS();
        delay(400);
      }*/
      sendGPS();
      delay(400);
      while(1); //Stop
    }

    else{ //ยังไม่ล้ม
      //การอ่านค่าsensorลองไปดูในไฟล์esp32_IMU ได้
      if((a.acceleration.x >= 7.00)||(a.acceleration.x <= -7.00)){
        Serial.println("Fall Detection acceleration x");
        sendGPS(); //ส่งตำแหน่ง
        delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
        count_fall++;
        //while(1);
      }

      else if((a.acceleration.y >= 7.00)||(a.acceleration.y <= -7.00)){
        Serial.println("Fall Detection acceleration y");
        sendGPS(); //ส่งตำแหน่ง
        delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
        count_fall++;
        //while(1);
      }

      else if((a.acceleration.z <= -9.00)){
        Serial.println("Fall Detection acceleration z");
        sendGPS(); //ส่งตำแหน่ง
        delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
        count_fall++;
        //while(1);
      }
    }

  /*int raw = analogRead(36); // อ่านค่า ADC จากพิน GPIO36 (ADC1_CHANNEL_0)
  float voltage = (raw / 4095.0) * V_REF;

  if(voltage>=V_REF){
    if(start_ESP32==0){ //Status is on
    sendToGoogleSheets(0.0,0.0);
    start_ESP32++;
    }  
      //Reading MPU sensor (ตอนนี้ใช้แค่ acceleration)
    sensors_event_t a, g, temp; //ตัวแปร acceleration,gyro,temp
    mpu.getEvent(&a, &g, &temp);

    if(count_fall!=0){ //ถ้าล้มแล้วsensorIMUหยุดจับไปแล้วยังคงต้องส่งตำแหน่งอยู่ไม่งั้นมันไม่ส่งตำแหน่ง
      Serial.println("Already Fall");
      for(int i=0; i<3; i++){
       sendGPS(); //ส่งตำแหน่ง
      }
      while(1); //Stop working
    }

    else{ //ยังไม่ล้ม
      //การอ่านค่าsensorลองไปดูในไฟล์esp32_IMU ได้
      if((a.acceleration.x >= 7.00)||(a.acceleration.x <= -7.00)){
        Serial.println("Fall Detection acceleration x");
        sendGPS(); //ส่งตำแหน่ง
        count_fall++;
        //while(1);
      }

      else if((a.acceleration.y >= 7.00)||(a.acceleration.y <= -7.00)){
        Serial.println("Fall Detection acceleration y");
        sendGPS(); //ส่งตำแหน่ง
        count_fall++;
        //while(1);
      }

      else if((a.acceleration.z <= -9.00)){
        Serial.println("Fall Detection acceleration z");
        sendGPS(); //ส่งตำแหน่ง
        count_fall++;
        //while(1);
      }
    }
  }

  else{
    sendToGoogleSheets(1.0,1.0); //clear sheet
    start_ESP32 = 0; //Reset value
  }*/

}


void sendGPS(){
    //Read gps 
    while (mygps.available() > 0) {
    gps.encode(mygps.read());

    if (gps.location.isUpdated()) {
      float Latitude = gps.location.lat();
      float Longitude = gps.location.lng();

      Serial.print("Latitude= ");
      Serial.print(Latitude, 6);
      Serial.print(", Longitude= ");
      Serial.println(Longitude, 6);

      sendToGoogleSheets(Latitude, Longitude);
    }
  }
}


void sendToGoogleSheets(float lat, float lng) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = "https://script.google.com/macros/s/AKfycbzRr6TcIoMDhJ2BpVM6IyQcCCogdsLQ9ObXI-jYD3fxwRo3HbcBoN1n9JOCmN5Gdy6n5w/exec?latitude=" + String(lat, 6) + "&longitude=" + String(lng, 6);
    Serial.println("Sending to:");
    Serial.println(url);

    http.begin(url.c_str());
    int httpCode = http.GET();
    delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
    
    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println(httpCode);
      Serial.println(payload);
    } else {
      Serial.println("Error on HTTP request");
    }

    http.end();
  }
}


void SetMPU6050(){
  while (!Serial)
    delay(10); // will pause Zero, Leonardo, etc until serial console opens

  //Serial.println("Adafruit MPU6050 test!");

  // Try to initialize!
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G); //Accelerometer range set
  mpu.setGyroRange(MPU6050_RANGE_500_DEG); //Gyro range set
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ); //Filter bandwidth set
}
