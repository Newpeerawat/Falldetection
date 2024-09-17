#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

#include <HTTPClient.h>


const char* ssid = "ctpproducts 2G"; //ESP32 IP Address: 192.168.1.50
const char* password = "sena8011";
void reconnect();

/*const char* ssid = "Newpeerawat"; //ESP32 IP Address: 192.168.42.102
const char* password = "New@3103"; //IP Address mobile: 10.36.14.71*/


/*//Gps Function
// สร้างวัตถุ TinyGPSPlus
TinyGPSPlus gps;

// กำหนดพินที่ใช้สำหรับการเชื่อมต่อ GPS กับ ESP32
// GPS Tx -> RX pin of ESP32 (e.g., GPIO 16)
// GPS Rx -> TX pin of ESP32 (e.g., GPIO 17)
HardwareSerial mygps(1); // ใช้ UART1
void sendGPS();*/

String Web_App_URL = "https://script.google.com/macros/s/AKfycbxrv863W7gFUye5UsqirA5xTAd8H6cMKV17xufAUJRHiCBj7QgsDwCLkrnx0GLhYi0q/exec";
void sendToGoogleSheets(float lat, float lng);


//MPU Function
Adafruit_MPU6050 mpu;
void SetMPU6050();

//Count function
int count_fall=0;
//int start_ESP32=0;

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

  //Set up MPU
  SetMPU6050();

  sendToGoogleSheets(0.0,0.0); //Send status esp32 on
  delay(1000);
}


void loop()
{ 
  //Reading MPU sensor (ตอนนี้ใช้แค่ acceleration)
  sensors_event_t a, g, temp; //ตัวแปร acceleration,gyro,temp
  mpu.getEvent(&a, &g, &temp);

  //การอ่านค่าsensorลองไปดูในไฟล์esp32_IMU ได้
    if((a.acceleration.x >= 7.00)||(a.acceleration.x <= -7.00)){
      Serial.println("Fall Detection acceleration x");
      //sendGPS(); //ส่งตำแหน่ง
      sendToGoogleSheets(1.0,1.0); //ส่งตำแหน่ง
      delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
      count_fall++;
      //while(1);
    }

    else if((a.acceleration.y >= 7.00)||(a.acceleration.y <= -7.00)){
      Serial.println("Fall Detection acceleration y");
      //sendGPS(); //ส่งตำแหน่ง
      sendToGoogleSheets(1.0,1.0); //ส่งตำแหน่ง
      delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
      count_fall++;
      //while(1);
    }

    else if((a.acceleration.z <= -9.00)){
      Serial.println("Fall Detection acceleration z");
      //sendGPS(); //ส่งตำแหน่ง
      sendToGoogleSheets(1.0,1.0); //ส่งตำแหน่ง
      delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
      count_fall++;
      //while(1);
    }


  /* 
  if(start_ESP32==0){ //Status is on
    sendToGoogleSheets(0.0,0.0);
    start_ESP32++;
  }  
      //Reading MPU sensor (ตอนนี้ใช้แค่ acceleration)
    sensors_event_t a, g, temp; //ตัวแปร acceleration,gyro,temp
    mpu.getEvent(&a, &g, &temp);

    if(count_fall!=0){ //ถ้าล้มแล้วsensorIMUหยุดจับไปแล้วยังคงต้องส่งตำแหน่งอยู่ไม่งั้นมันไม่ส่งตำแหน่ง
      Serial.println("Already Fall");
      for(int i=0; i<2; i++){
        sendGPS();//ส่งตำแหน่ง
        delay(400);
      }
      //sendGPS();
      delay(400);
      while(1); //Stop
    }

    else{ 
      //การอ่านค่าsensorลองไปดูในไฟล์esp32_IMU ได้
      if((a.acceleration.x >= 7.00)||(a.acceleration.x <= -7.00)){
        Serial.println("Fall Detection acceleration x");
        //sendGPS(); //ส่งตำแหน่ง
        delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
        count_fall++;
        //while(1);
      }

      else if((a.acceleration.y >= 7.00)||(a.acceleration.y <= -7.00)){
        Serial.println("Fall Detection acceleration y");
        //sendGPS(); //ส่งตำแหน่ง
        delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
        count_fall++;
        //while(1);
      }

      else if((a.acceleration.z <= -9.00)){
        Serial.println("Fall Detection acceleration z");
        //sendGPS(); //ส่งตำแหน่ง
        delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
        count_fall++;
        //while(1);
      }
    }*/
}


void reconnect(){
  // ตัดการเชื่อมต่อ Wi-Fi
  WiFi.disconnect();
  delay(1000);  // รอ 1 วินาที

  // เชื่อมต่อ Wi-Fi ใหม่
  WiFi.begin(ssid, password);

  // รอจนกว่าเชื่อมต่อ Wi-Fi จะสำเร็จ
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Reconnecting to WiFi...");
  }

  Serial.println("Reconnected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
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


void sendToGoogleSheets(float lat, float lng){
  if (WiFi.status() == WL_CONNECTED) {
    // Create a URL for sending or writing data to Google Sheets.
    String Send_Data_URL = Web_App_URL + "?sts=write";
    Send_Data_URL += "&latitude=" + String(lat,6);
    Send_Data_URL += "&longitude=" + String(lng,6);

    //Send_Data_URL += "&srs=" + Status_Read_Sensor;
    //Send_Data_URL += "&temp=" + String(Temp);
    //Send_Data_URL += "&humd=" + String(Humd);
    //Send_Data_URL += "&swtc1=" + Switch_1_State;
    //Send_Data_URL += "&swtc2=" + Switch_2_State;

    Serial.println();
    Serial.println("-------------");
    Serial.println("Send data to Google Spreadsheet...");
    Serial.print("URL : ");
    Serial.println(Send_Data_URL);

    //::::::::::::::::::The process of sending or writing data to Google Sheets.
      // Initialize HTTPClient as "http".
      HTTPClient http;
  
      // HTTP GET Request.
      http.begin(Send_Data_URL.c_str());
      http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  
      // Gets the HTTP status code.
      int httpCode = http.GET(); 
      Serial.print("HTTP Status Code : ");
      Serial.println(httpCode);

      delay(400); //ใส่เพื่อหน่วงให้เวลาส่งgps
      // Getting response from google sheets.
      String payload;
      if (httpCode > 0) {
        payload = http.getString();
        Serial.println("Payload : " + payload);    
      } else {
        Serial.println("Error on HTTP request");
        reconnect();
    }
      
      http.end();

    Serial.println("-------------");
  }
}


/*void sendToGoogleSheets(float lat, float lng) {
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
      reconnect();
    }

    http.end();
  }
}*/


/*void sendGPS(){
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
}*/
