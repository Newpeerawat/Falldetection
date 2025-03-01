#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>


// ข้อมูล WiFi
const char* ssid = "ctpproducts 2G";
const char* password = "sena8011";


// URL ของ API
const char* serverName = "http://192.168.1.50:5000/predict";


//Google sheet function
void reconnect();
String Web_App_URL = "https://script.google.com/macros/s/AKfycbxrv863W7gFUye5UsqirA5xTAd8H6cMKV17xufAUJRHiCBj7QgsDwCLkrnx0GLhYi0q/exec";
void sendToGoogleSheets(float lat, float lng);


//MPU Function
Adafruit_MPU6050 mpu;
void SetMPU6050();


//Set Buzzer
int Buzzer = 23;


/*
// ข้อมูล WiFi
const char* ssid = "Newpeerawat";
const char* password = "New@3103";

// URL ของ API
const char* serverName = "http://192.168.218.238:5000/predict";
*/

/*
// ข้อมูล WiFi
const char* ssid = "Himeka";
const char* password = "15072546";

// URL ของ API
const char* serverName = "http://172.20.10.3:5000/predict";
*/


void setup() {
  Serial.begin(115200);
  pinMode(Buzzer,OUTPUT);

  // เชื่อมต่อ WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  //Set up MPU
  SetMPU6050();

  sendToGoogleSheets(0.0,0.0); //Send status esp32 on
  delay(1000);
}


void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    /* Get new sensor events with the readings */
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    //Store acceleration
    float AccX = a.acceleration.x;
    float AccY = a.acceleration.y;
    float AccZ = a.acceleration.z;

    //m/s^2 to g
    AccX = AccX/9.80665;
    AccY = AccY/9.80665;
    AccZ = AccZ/9.80665;

    //Store gyro
    float GyrX = g.gyro.x;
    float GyrY = g.gyro.y;
    float GyrZ = g.gyro.z;

    //rad/s to deg/s
    GyrX = GyrX*57.29578;
    GyrY = GyrY*57.29578;
    GyrZ = GyrZ*57.29578;

    HTTPClient http;

    // เชื่อมต่อไปยังเซิร์ฟเวอร์
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    // สร้าง JSON Payload
    String jsonPayload = "{\"inputs\":[" + 
                         String(AccX) + "," +
                         String(AccY) + "," +
                         String(AccZ) + "," +
                         String(GyrX) + "," +
                         String(GyrY) + "," +
                         String(GyrZ) + "]}";

    // ส่ง POST Request
    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      //Serial.println("Response: " + response);
      if (response.indexOf("No Fall") >= 0) {
        Serial.println("No Fall detected.");
      }
      else if (response.indexOf("Fall") >= 0) {
        Serial.println("Fall detected send to gps.....");
        sendToGoogleSheets(1.0,1.0); 
        //delay(400);
        while(1){
          tone(Buzzer,1661); //Buzzer On
          delay(2000);
          tone(Buzzer,0); //Buzzer Off
          delay(3000);
        } 
      }
      
    } else {
      Serial.println("Error sending request");
    }

    http.end();
  }
  delay(100); // รอ 100 วินาที
}


void reconnect(){
  // ตัดการเชื่อมต่อ Wi-Fi
  WiFi.disconnect();
  delay(1000);  // รอ 1 วินาที

  // เชื่อมต่อ Wi-Fi ใหม่
  WiFi.begin(ssid, password);

  // รอจนกว่าเชื่อมต่อ Wi-Fi จะสำเร็จ
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
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