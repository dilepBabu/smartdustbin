#include <WiFi.h>
#include <ESP32Servo.h>
#include <Firebase_ESP_Client.h>

// Firebase Helper Addons
#include <addons/TokenHelper.h>
#include <addons/RTDBHelper.h>

/* WiFi credentials */
#define WIFI_SSID "Esp32"
#define WIFI_PASSWORD "Connected"

/* Firebase credentials */
#define API_KEY "AIzaSyDqZeNzpNMUaA3v3ACB5M9xC41uTBOFrSA"
#define DATABASE_URL "https://smart-dustbin-75385-default-rtdb.asia-southeast1.firebasedatabase.app/"

/* Firebase Authentication */
#define USER_EMAIL "dilepbabu2003@gmail.com"
#define USER_PASSWORD "123456"

// Firebase objects
FirebaseData firebaseData;
FirebaseAuth auth;
FirebaseConfig config;

// IR sensor and servo pins
const int irSensorPin = 33;
bool detectedOnce = false;

Servo servo1;
Servo servo2;

void setup() {
  Serial.begin(115200);
  pinMode(irSensorPin, INPUT);

  servo1.attach(12);
  

  servo1.write(0);
  servo2.write(0);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\nWiFi Connected!");

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("System Ready!");
}

void loop() {
  if (Firebase.RTDB.getString(&firebaseData, "/waste_disposal/Ready")) {
    String readyStatus = firebaseData.stringData();
    Serial.println("Ready Status: " + readyStatus);

    if (readyStatus == "start" && !detectedOnce) {
        servo1.write(0);
      if (digitalRead(irSensorPin) == LOW) {
        Serial.println("Trash detected!");

        // Move both servos to 90°
        
        

        Firebase.RTDB.setBool(&firebaseData, "/waste_disposal/Status", true);
        detectedOnce = true;

        delay(5000); // Wait before resetting

        // Move both servos back to 0°
       

        Firebase.RTDB.setBool(&firebaseData, "/waste_disposal/Status", false);
        Serial.println("Status reset to false.");
      }
    } else if (readyStatus != "start") {
      detectedOnce = false;
      servo1.write(90);
     
      Serial.println("Ready not start, servos reset.");
    }

  } else {
    Serial.print("Error getting Ready status: ");
    Serial.println(firebaseData.errorReason());
  }

  delay(1000);
}
