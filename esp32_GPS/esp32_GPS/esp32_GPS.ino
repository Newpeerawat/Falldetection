#include <TinyGPS++.h>

// สร้างวัตถุ TinyGPSPlus
TinyGPSPlus gps;

// กำหนดพินที่ใช้สำหรับการเชื่อมต่อ GPS กับ ESP32
// GPS Tx -> RX pin of ESP32 (e.g., GPIO 16)
// GPS Rx -> TX pin of ESP32 (e.g., GPIO 17)
HardwareSerial mygps(1); // ใช้ UART1

char latitude[20];
char longitude[20];
#define MAX_DIGITS_FRAC 6 // Maximum number of digits in the fractional part

void floatToString(float num, char *str) {
	// Extract integer part
	int intPart = (int)num;

	// Extract fractional part
	float fracPart = num - intPart;

	// Convert integer part to string
	int index = 0;
	if (intPart == 0) {
		str[index++] = '0'; // Handle case when number is less than 1
		} else {
		while (intPart > 0) {
			str[index++] = '0' + (intPart % 10);
			intPart /= 10;
		}
	}
	// Reverse the integer part string
	int i;
	for (i = 0; i < index / 2; i++) {
		char temp = str[i];
		str[i] = str[index - i - 1];
		str[index - i - 1] = temp;
	}

	// Add decimal point
	str[index++] = '.';

	// Convert fractional part to string
	int fracIndex = 0;
	while (fracIndex < MAX_DIGITS_FRAC) {
		fracPart *= 10;
		int digit = (int)fracPart;
		str[index++] = '0' + digit;
		fracPart -= digit;
		fracIndex++;
	}

	// Null-terminate the string
	str[index] = '\0';
}

void setup(){
  // เริ่มต้น Serial สำหรับการติดต่อสื่อสารกับคอมพิวเตอร์
  Serial.begin(115200);
  
  // เริ่มต้น mygps สำหรับการติดต่อสื่อสารกับโมดูล GPS
  // โดยใช้พอร์ต 1 ของ ESP32 (TX = 17, RX = 16)
  mygps.begin(9600, SERIAL_8N1, 16, 17); // บิตต่อวินาที, รูปแบบข้อมูล, RX, TX

}

void loop(){
  // ตรวจสอบข้อมูลจากโมดูล GPS
  while (mygps.available() > 0){
    gps.encode(mygps.read());
    
    if (gps.location.isUpdated()){
      // อ่านข้อมูลตำแหน่ง
      float Latitude = gps.location.lat();
      float Longitude = gps.location.lng();

      // แสดงข้อมูลตำแหน่งแบบfloat
      Serial.println("Float");
      Serial.print("Latitude= ");  
      Serial.print(Latitude, 6); // ทศนิยม 6 ตำแหน่ง
      Serial.print(", Longitude= "); 
      Serial.println(Longitude, 6);

      // แสดงข้อมูลตำแหน่งแบบstring
      Serial.println("String");
      floatToString(Latitude,latitude);
      floatToString(Longitude,longitude);
   
      Serial.print("Latitude= ");
      Serial.print(latitude);
      Serial.print(", Longitude= "); 
      Serial.println(longitude);
    }
  }
}
