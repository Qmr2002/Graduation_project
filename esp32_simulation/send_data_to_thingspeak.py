import json
import requests
import random
import time
import os

# ThingSpeak API Details
THINGSPEAK_WRITE_API = "P1E6IR6D62KSYNAD"  # Your Write API Key
THINGSPEAK_URL = "https://api.thingspeak.com/update"
PUMP_STATUS_FILE = "../backend/pump_status.json"  # Path to pump status

# Ensure pump_status.json exists
if not os.path.exists(PUMP_STATUS_FILE):
    with open(PUMP_STATUS_FILE, "w") as f:
        json.dump({"pump": 0}, f)

# Function to read stored pump status BEFORE SENDING DATA
def read_pump_status():
    try:
        with open(PUMP_STATUS_FILE, "r") as f:
            status = json.load(f)["pump"]
            print(f"✅ Read Pump Status from JSON: {status}")  # Debugging Log
            return status
    except (FileNotFoundError, json.JSONDecodeError):
        return 0  # Default to OFF

# Function to generate simulated sensor readings
def get_sensor_data():
    pump_status = read_pump_status()
    print(f"✅ ESP32 Read Pump Status: {pump_status}")  # Debugging Log

    return {
        "soil_moisture": round(random.uniform(20, 80), 2),
        "temperature": round(random.uniform(20, 35), 2),
        "humidity": round(random.uniform(30, 70), 2),
        "irrigation": pump_status  # ✅ This should match pump_status.json!
    }

# Function to send data to ThingSpeak
def send_to_thingspeak():
    while True:
        data = get_sensor_data()
        payload = {
            "api_key": THINGSPEAK_WRITE_API,
            "field1": data["soil_moisture"],
            "field2": data["temperature"],
            "field3": data["humidity"],
            "field4": data["irrigation"]  # ✅ Sends actual pump status
        }

        response = requests.get(THINGSPEAK_URL, params=payload)

        if response.status_code == 200:
            print("✅ Data successfully sent to ThingSpeak:", data)
        else:
            print("❌ Error sending data:", response.text)

        time.sleep(15)  # Send data every 15 seconds

if __name__ == "__main__":
    send_to_thingspeak()
