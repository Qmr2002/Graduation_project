import requests

# ThingSpeak API Details
THINGSPEAK_READ_API = "YN19K3YFAH13IGDD"  # Your Read API Key
THINGSPEAK_CHANNEL_ID = "2845035"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

# Function to read the latest sensor data from ThingSpeak
def read_from_thingspeak():
    response = requests.get(THINGSPEAK_URL, params={"api_key": THINGSPEAK_READ_API, "results": 1})

    if response.status_code == 200:
        data = response.json()["feeds"][0]
        print("✅ Latest Data from ThingSpeak:")
        print(f"Soil Moisture: {data['field1']}%")
        print(f"Temperature: {data['field2']}°C")
        print(f"Humidity: {data['field3']}%")
        print(f"Irrigation Status: {'ON' if data['field4'] == '1' else 'OFF'}")
    else:
        print("❌ Error retrieving data:", response.text)

if __name__ == "__main__":
    read_from_thingspeak()
