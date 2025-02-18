import requests
import random
import time

# ThingSpeak API Details
THINGSPEAK_WRITE_API = "P1E6IR6D62KSYNAD"  # Your Write API Key
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Function to generate simulated sensor readings
def get_sensor_data():
    return {
        "soil_moisture": round(random.uniform(20, 80), 2),  # Simulated soil moisture %
        "temperature": round(random.uniform(20, 35), 2),    # Simulated temperature °C
        "humidity": round(random.uniform(30, 70), 2),       # Simulated humidity %
        "irrigation": 1 if random.uniform(0, 100) < 30 else 0  # 1 = ON, 0 = OFF
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
            "field4": data["irrigation"]
        }

        response = requests.get(THINGSPEAK_URL, params=payload)

        if response.status_code == 200:
            print("✅ Data successfully sent to ThingSpeak:", data)
        else:
            print("❌ Error sending data:", response.text)

        time.sleep(15)  # Send data every 15 seconds

if __name__ == "__main__":
    send_to_thingspeak()
