#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ============== CONFIGURATION ==============
#define SOIL_SENSOR_PIN 34    // Capacitive sensor on GPIO34
#define RELAY_PIN 5           // Pump control on GPIO5
#define DRY_VALUE 4095        // Sensor in dry air
#define WET_VALUE 1350        // Sensor submerged in water
#define MOISTURE_THRESHOLD 30 // Automatic activation threshold (%)

// WiFi Credentials
const char* ssid = "Etisalat-3FChh";
const char* password = "G7mFPcF3";

// ThingSpeak Settings
const char* thingspeakAPI = "P1E6IR6D62KSYNAD";
const int channelID = 2845035;
const int commandField = 4;  // Changed from 2 to match server's field4
const int statusField = 4;   // Unified field for status

// ============== GLOBAL OBJECTS ==============
WiFiClient client;
HTTPClient http;
unsigned long lastCommandCheck = 0;

// ============== CUSTOM FUNCTIONS ==============
float readSoilMoisture() {
  // Fast median filtering (10 samples)
  const byte samples = 10;
  int readings[samples];
  for(byte i=0; i<samples; i++) {
    readings[i] = analogRead(SOIL_SENSOR_PIN);
    delay(1);
  }
  std::sort(readings, readings + samples);
  int raw = readings[samples/2];

  // Optimized calibration formula
  float normalized = 1.0 - ((raw - WET_VALUE) / (DRY_VALUE - WET_VALUE));
  float moisture = pow(constrain(normalized, 0.0f, 1.0f), 0.7) * 100;
  
  Serial.printf("[SENSOR] Raw: %d → Moisture: %.1f%%\n", raw, moisture);
  return moisture;
}

void connectToWiFi() {
  if(WiFi.status() == WL_CONNECTED) return;
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  unsigned long start = millis();
  while(WiFi.status() != WL_CONNECTED && millis()-start < 5000) { // 5s timeout
    delay(100);
    Serial.print(".");
  }
  
  if(WiFi.status() != WL_CONNECTED) {
    Serial.println("\nWiFi connection failed! Rebooting...");
    ESP.restart();
  }
  Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());
}

int getPumpCommand() {
  String url = "http://api.thingspeak.com/channels/" + String(channelID) + 
               "/fields/" + String(commandField) + "/last.json?api_key=" + String(thingspeakAPI);
  http.begin(url);
  int httpCode = http.GET();
  
  if(httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    int start = payload.indexOf("\"field"+String(commandField)+"\":\"") + 10;
    if(start < 10) return -1;
    int end = payload.indexOf("\"", start);
    if(end <= start) return -1;
    String cmd = payload.substring(start, end);
    return cmd.isEmpty() ? -1 : cmd.toInt();
  }
  http.end();
  return -1;
}

void updateSystemStatus(float moisture, bool pumpState) {
  String url = "http://api.thingspeak.com/update?api_key=" + String(thingspeakAPI) +
               "&field1=" + String(moisture, 1) +
               "&field4=" + String(pumpState);
  
  http.begin(url);
  int httpCode = http.GET();
  if(httpCode == HTTP_CODE_OK) {
    Serial.println("ThingSpeak update OK");
  } else {
    Serial.println("ThingSpeak update failed");
  }
  http.end();
}


void controlRelay(bool state) {
  digitalWrite(RELAY_PIN, state);
  Serial.printf("[RELAY] %s - %s\n", state ? "ON" : "OFF", state ? "🔊 CLICK!" : "");
  delay(50); // Ensure physical relay activation
}

void handleCommands(float moisture) {
  static bool autoMode = true;
  static unsigned long lastAutoUpdate = 0;
  
  if(millis() - lastCommandCheck >= 2000) {
    int command = getPumpCommand();
    
    if(command == 1 || command == 0) {  // Accept only 1/0 commands
      controlRelay(command);
      autoMode = false;
      lastAutoUpdate = millis();
      Serial.printf("Manual command: %d\n", command);
    }
    else if(!autoMode && (millis() - lastAutoUpdate > 30000)) {
      autoMode = true;
      Serial.println("Switching to Auto mode");
    }
    
    lastCommandCheck = millis();
  }

  // Automatic control
  if(autoMode) {
    static unsigned long lastMoistureCheck = 0;
    if(millis() - lastMoistureCheck >= 5000) {
      bool shouldActivate = moisture < MOISTURE_THRESHOLD;
      if(shouldActivate != digitalRead(RELAY_PIN)) {
        controlRelay(shouldActivate);
      }
      lastMoistureCheck = millis();
    }
  }
}
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  connectToWiFi();
}

void loop() {
  static unsigned long lastUpdate = 0;
  
  if(millis() - lastUpdate >= 1000) { // 1-second base interval
    connectToWiFi();
    
    float moisture = readSoilMoisture();
    if(!isnan(moisture)) {
      handleCommands(moisture);
      updateSystemStatus(moisture, digitalRead(RELAY_PIN));
    }
    
    lastUpdate = millis();
  }
}