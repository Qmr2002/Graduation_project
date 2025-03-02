from machine import Pin, ADC, Timer
import dht
import network
import urequests
import time
import json

# Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
THINGSPEAK_API_KEY = "YOUR_THINGSPEAK_WRITE_KEY"
CHANNEL_ID = "YOUR_CHANNEL_ID"

# Hardware Setup
d = dht.DHT22(Pin(4))          # DHT22 on GPIO4
soil_sensor = ADC(Pin(34))      # Soil moisture sensor
relay = Pin(5, Pin.OUT)         # Pump relay control

# Calibration Values (Adjust based on your sensor)
DRY_SOIL = 2500     # Analog value in dry soil
WET_SOIL = 1000     # Analog value in wet soil
MOISTURE_THRESHOLD = 30  # Percentage

# Global Variables
last_update = 0
wlan = network.WLAN(network.STA_IF)

def connect_wifi():
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        for _ in range(20):  # Wait up to 10 seconds
            if wlan.isconnected():
                break
            time.sleep(0.5)
        
        if wlan.isconnected():
            print("Connected! IP:", wlan.ifconfig()[0])
        else:
            print("Failed to connect to WiFi")

def read_sensors():
    try:
        d.measure()
        temp = d.temperature()
        hum = d.humidity()
    except OSError:
        print("Error reading DHT22")
        temp = hum = 0
    
    soil_raw = soil_sensor.read()
    moisture_pct = max(0, min(100, 
        int((soil_raw - DRY_SOIL) * 100 / (WET_SOIL - DRY_SOIL))
    
    return moisture_pct, temp, hum

def get_pump_status():
    try:
        url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/4/last.json"
        response = urequests.get(url)
        data = json.loads(response.text)
        return int(data["field4"])
    except:
        return 0

def send_to_thingspeak(moisture, temp, hum):
    url = (
        "https://api.thingspeak.com/update?"
        f"api_key={THINGSPEAK_API_KEY}&"
        f"field1={moisture}&"
        f"field2={temp}&"
        f"field3={hum}"
    )
    try:
        response = urequests.get(url)
        print("Data sent. Response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)

def main_loop(timer):
    global last_update
    
    if time.ticks_diff(time.ticks_ms(), last_update) >= 15000:
        connect_wifi()
        
        if wlan.isconnected():
            moisture, temp, hum = read_sensors()
            pump_status = get_pump_status()
            
            # Control pump
            if pump_status == 1 or moisture < MOISTURE_THRESHOLD:
                relay.value(1)
            else:
                relay.value(0)
            
            send_to_thingspeak(moisture, temp, hum)
            last_update = time.ticks_ms()

# Initialize
timer = Timer(-1)
timer.init(period=1000, mode=Timer.PERIODIC, callback=main_loop)