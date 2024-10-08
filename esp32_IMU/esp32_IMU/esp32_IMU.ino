#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
void SetMPU6050();

void setup(void) {
  Serial.begin(115200);
  SetMPU6050();
}

void loop() {
  /* Get new sensor events with the readings */
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  if((a.acceleration.x >= 7.00)||(a.acceleration.x <= -7.00)){
    Serial.println("Fall Detection acceleration x");
  }

  else if((a.acceleration.y >= 7.00)||(a.acceleration.y <= -7.00)){
    Serial.println("Fall Detection acceleration y");
  }

  else if((a.acceleration.z <= -9.00)){
    Serial.println("Fall Detection acceleration z");
  }

  // Print out the values 
  /*Serial.print("Acceleration X: ");
  Serial.print(a.acceleration.x);
  Serial.print(", Y: ");
  Serial.print(a.acceleration.y);
  Serial.print(", Z: ");
  Serial.print(a.acceleration.z);
  Serial.println(" m/s^2");*/

  /*Serial.print("Rotation X: ");
  Serial.print(g.gyro.x);
  Serial.print(", Y: ");
  Serial.print(g.gyro.y);
  Serial.print(", Z: ");
  Serial.print(g.gyro.z);
  Serial.println(" rad/s");

  Serial.print("Temperature: ");
  Serial.print(temp.temperature);
  Serial.println(" degC");*/

  Serial.println("");
  delay(500);
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
