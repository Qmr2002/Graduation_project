#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// Sensor & Pin Definitions
#define DHTPIN 4          // DHT22 on GPIO4
#define DHTTYPE DHT22
#define SOIL_MOISTURE_PIN 34  // Analog pin for soil sensor
#define RELAY_PIN 5       // Relay control for pump

// WiFi Credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// ThingSpeak Settings
const char* thingspeakApiKey = "YOUR_THINGSPEAK_WRITE_API";
const char* thingspeakURL = "http://api.thingspeak.com/update";
const int channelID = YOUR_CHANNEL_ID;  // Replace with your channel ID

// Global Objects
DHT dht(DHTPIN, DHTTYPE);
HTTPClient http;

// Thresholds
const int DRY_SOIL = 2500;   // Calibrate these values!
const int WET_SOIL = 1000;
const int MOISTURE_THRESHOLD = 30;  // Percentage

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  dht.begin();
  
  connectToWiFi();
}

void loop() {
  static unsigned long lastUpdate = 0;
  
  if (millis() - lastUpdate >= 15000) {  // 15-second interval
    // Read sensors
    float moisture = analogRead(SOIL_MOISTURE_PIN);
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    // Convert soil moisture to percentage
    int moisturePercent = map(moisture, DRY_SOIL, WET_SOIL, 0, 100);
    moisturePercent = constrain(moisturePercent, 0, 100);

    // Get pump status from ThingSpeak (Field4)
    int pumpStatus = getPumpStatusFromThingSpeak();

    // Control pump based on status or auto-mode
    if (pumpStatus == 1 || moisturePercent < MOISTURE_THRESHOLD) {
      digitalWrite(RELAY_PIN, HIGH);
    } else {
      digitalWrite(RELAY_PIN, LOW);
    }

    // Send data to ThingSpeak
    sendToThingSpeak(moisturePercent, temperature, humidity);
    
    lastUpdate = millis();
  }
}

// Connect/reconnect to WiFi
void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP());
}

// Send sensor data to ThingSpeak (Fields1-3)
void sendToThingSpeak(float moisture, float temp, float humidity) {
  String url = String(thingspeakURL) + 
               "?api_key=" + thingspeakApiKey +
               "&field1=" + String(moisture) +
               "&field2=" + String(temp) +
               "&field3=" + String(humidity);

  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    Serial.println("Data sent to ThingSpeak");
  } else {
    Serial.println("HTTP Error: " + String(httpCode));
  }
  http.end();
}

// Read pump status from ThingSpeak (Field4)
int getPumpStatusFromThingSpeak() {
  String url = "http://api.thingspeak.com/channels/" + String(channelID) + 
               "/fields/4/last.json";
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    int start = payload.indexOf("\"field4\":\"") + 9;
    int end = payload.indexOf("\"", start);
    String status = payload.substring(start, end);
    return status.toInt();
  }
  return 0;  // Default to OFF
}