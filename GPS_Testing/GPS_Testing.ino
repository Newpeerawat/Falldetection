#include <TinyGPS++.h>
#include <SoftwareSerial.h>
TinyGPSPlus gps;
SoftwareSerial mygps(4,3); // GPS Tx Pin - D4  GPS Rx Pin D3

void setup(){
  Serial.begin(9600);
  mygps.begin(9600);
}

void loop(){
  // This sketch displays information every time a new sentence is correctly encoded.
  while (mygps.available() > 0){
    gps.encode(mygps.read());
    if (gps.location.isUpdated()){
      float Latitude = gps.location.lat();
      float Longitude = gps.location.lng();

      Serial.print("Latitude= ");  
      Serial.print(Latitude, 6); //ทศนิยม 6 ตำแหน่ง
      Serial.print("Longitude= "); 
      Serial.println(Longitude, 6);
      }
       
    }
   
}

