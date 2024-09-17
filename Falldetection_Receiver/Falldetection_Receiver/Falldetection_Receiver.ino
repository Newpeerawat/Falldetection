#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#include <TinyGPS++.h>

#include <Adafruit_Sensor.h>
#include <Wire.h>

#include <HTTPClient.h>


const char* ssid = "ctpproducts 2G"; //ESP32 IP Address: 192.168.1.50
const char* password = "sena8011";
void reconnect();

/*const char* ssid = "Newpeerawat"; //ESP32 IP Address: 192.168.42.102
const char* password = "New@3103"; //IP Address mobile: 10.36.14.71*/


//Gps Function
// สร้างวัตถุ TinyGPSPlus
TinyGPSPlus gps;

// กำหนดพินที่ใช้สำหรับการเชื่อมต่อ GPS กับ ESP32
// GPS Tx -> RX pin of ESP32 (e.g., GPIO 16)
// GPS Rx -> TX pin of ESP32 (e.g., GPIO 17)
HardwareSerial mygps(1); // ใช้ UART1
void sendGPS();

String Web_App_URL = "https://script.google.com/macros/s/AKfycbxrv863W7gFUye5UsqirA5xTAd8H6cMKV17xufAUJRHiCBj7QgsDwCLkrnx0GLhYi0q/exec";
float receiveToGoogleSheets();
void sendToGoogleSheets(float lat, float lng);
float receive;
float latitude;
float longitude;

//________________________________________________________________________________getValue()
// String function to process the data (Split String).
// I got this from : https://www.electroniclinic.com/reyax-lora-based-multiple-sensors-monitoring-using-arduino/
String getValue(String data, char separator, int index) {
  int found = 0;
  int strIndex[] = { 0, -1 };
  int maxIndex = data.length() - 1;
  
  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == separator || i == maxIndex) {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i+1 : i;
    }
  }
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
//________________________________________________________________________________ 


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

  //Set up Gps
  // เริ่มต้น mygps สำหรับการติดต่อสื่อสารกับโมดูล GPS
  // โดยใช้พอร์ต 1 ของ ESP32 (TX2 = 17, RX2 = 16)
  mygps.begin(9600, SERIAL_8N1, 16, 17); // บิตต่อวินาที, รูปแบบข้อมูล, RX, TX*/

}


void loop()
{ 
  receive = receiveToGoogleSheets();
  if(receive==1){
    sendGPS();
  }
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


float receiveToGoogleSheets(){
  if (WiFi.status() == WL_CONNECTED){
    // Create a URL for reading or getting data from Google Sheets.
    String Read_Data_URL = Web_App_URL + "?sts=read";
    Serial.println();
    Serial.println("-------------");
    Serial.println("Read data from Google Spreadsheet...");
    Serial.print("URL : ");
    Serial.println(Read_Data_URL);

    //::::::::::::::::::The process of reading or getting data from Google Sheets.
    // Initialize HTTPClient as "http".
    HTTPClient http;
    // HTTP GET Request.
      http.begin(Read_Data_URL.c_str());
      http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);

      // Gets the HTTP status code.
      int httpCode = http.GET(); 
      Serial.print("HTTP Status Code : ");
      Serial.println(httpCode);
  
      // Getting response from google sheet.
      String payload;
      if (httpCode > 0) {
        payload = http.getString();
        Serial.println("Payload : " + payload);  
      }
  
      http.end();
    //::::::::::::::::::

    //::::::::::::::::::Conditions that are executed if reading or getting data from Google Sheets is successful (HTTP Status Codes : 200).
    if (httpCode == 200){
      latitude = getValue(payload, ',', 0).toFloat();
      longitude = getValue(payload, ',', 1).toFloat();
      //Serial.println(latitude);
      //Serial.println(longitude);
    }else{
      reconnect();
    }

  }

  return latitude;
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


void sendToGoogleSheets(float lat, float lng){
  if (WiFi.status() == WL_CONNECTED) {
    // Create a URL for sending or writing data to Google Sheets.
    String Send_Data_URL = Web_App_URL + "?sts=write";
    Send_Data_URL += "&reallatitude=" + String(lat,6);
    Send_Data_URL += "&reallongitude=" + String(lng,6);

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
