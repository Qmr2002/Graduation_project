import json
import requests
import random
import time
import os

# ThingSpeak API Keys
THINGSPEAK_WRITE_API = "P1E6IR6D62KSYNAD"
THINGSPEAK_READ_API = "YN19K3YFAH13IGDD"
THINGSPEAK_CHANNEL_ID = "2845035"

PUMP_STATUS_FILE = "../backend/pump_status.json"  # Path to local pump status

# Ensure file exists
if not os.path.exists(PUMP_STATUS_FILE):
    with open(PUMP_STATUS_FILE, "w") as f:
        json.dump({"pump": 0}, f)  # Default OFF

# Function to read the latest pump status
def read_pump_status():
    try:
        with open(PUMP_STATUS_FILE, "r") as f:
            return json.load(f)["pump"]
    except (FileNotFoundError, json.JSONDecodeError):
        return 0  # Default OFF


def send_to_thingspeak():
    while True:
        pump_status = read_pump_status()  # ✅ Read latest status before sending data

        # Simulated sensor readings
        data = {
            "soil_moisture": round(random.uniform(20, 80), 2),
            "temperature": round(random.uniform(20, 35), 2),
            "humidity": round(random.uniform(30, 70), 2),
            "irrigation": pump_status
        }

        # ✅ Send data to ThingSpeak
        response = requests.get(
            "https://api.thingspeak.com/update",
            params={
                "api_key": THINGSPEAK_WRITE_API,
                "field1": data["soil_moisture"],
                "field2": data["temperature"],
                "field3": data["humidity"],
                "field4": data["irrigation"]
            }
        )

        if response.status_code == 200:
            print("✅ Data sent:", data)
        else:
            print("❌ Error:", response.text)

        time.sleep(15)  # Send every 15 seconds


if __name__ == "__main__":
    send_to_thingspeak()
