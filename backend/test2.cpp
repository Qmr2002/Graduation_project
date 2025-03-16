#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ============== HARDWARE CONFIG ==============
#define SOIL_SENSOR_PIN 34
#define RELAY_PIN 5
#define MOISTURE_THRESHOLD 30  // Pump activation threshold (%)

// WiFi Credentials
const char* ssid = "SI";
const char* password = "1234567890";

// Server Configuration
const char* SERVER = "http://your-local-ip:5000"; // Your Flask server address
const unsigned long UPDATE_INTERVAL = 2000; // 2 seconds

// ============== GLOBAL OBJECTS ==============
WiFiClient client;
HTTPClient http;

// ============== FUNCTION PROTOTYPES ==============
float readSoilMoisture();
String getPumpStatus();
void controlPump(float moisture, String command);
void sendSensorData(float moisture);

// ============== SENSOR FUNCTIONS ==============
float readSoilMoisture() {
  // Static calibration values (adjust according to your sensor)
  const int AIR_VALUE = 4095;   // Sensor in air (dry)
  const int WATER_VALUE = 1350; // Sensor in water (wet)
  
  int raw = analogRead(SOIL_SENSOR_PIN);
  
  // Validate sensor connection
  if(raw < 100 || raw > 4000) {
    Serial.println("[ERROR] Check sensor connection!");
    return -1.0;
  }

  // Calculate moisture percentage
  float moisture = constrain(
    map(raw, AIR_VALUE, WATER_VALUE, 0, 100), 
    0, 100
  );

  Serial.printf("[SENSOR] Raw: %d → Moisture: %.1f%%\n", raw, moisture);
  return moisture;
}

// ============== PUMP CONTROL ==============
void controlPump(float moisture, String command) {
  static bool autoMode = true;
  
  // Manual override
  if(command != "auto") {
    autoMode = false;
    digitalWrite(RELAY_PIN, command == "on" ? HIGH : LOW);
    Serial.printf("[PUMP] Manual %s\n", command.c_str());
    return;
  }

  // Automatic control
  autoMode = true;
  bool shouldActivate = moisture < MOISTURE_THRESHOLD;
  digitalWrite(RELAY_PIN, shouldActivate ? HIGH : LOW);
  if(shouldActivate) Serial.println("[PUMP] Auto ON");
}

// ============== COMMUNICATION ==============
String getPumpStatus() {
  String url = String(SERVER) + "/api/pump_status";
  
  http.begin(client, url);
  int code = http.GET();
  
  if(code == HTTP_CODE_OK) {
    return http.getString();
  }
  return "auto";
}

void sendSensorData(float moisture) {
  if(moisture < 0) return;
  
  String url = String(SERVER) + "/api/update?moisture=" + String(moisture);
  
  http.begin(client, url);
  http.GET();
  http.end();
}

// ============== MAIN FUNCTIONS ==============
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
}

void loop() {
  static unsigned long lastUpdate = 0;
  
  if(millis() - lastUpdate >= UPDATE_INTERVAL) {
    float moisture = readSoilMoisture();
    String pumpCommand = getPumpStatus();
    
    if(moisture >= 0) {
      controlPump(moisture, pumpCommand);
      sendSensorData(moisture);
    }
    
    lastUpdate = millis();
  }
}