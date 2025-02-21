from flask import Flask, render_template, jsonify, request
import requests
import json
import os

app = Flask(__name__)

# ThingSpeak API Keys
THINGSPEAK_WRITE_API = "P1E6IR6D62KSYNAD"  # Your Write API Key
THINGSPEAK_READ_API = "YN19K3YFAH13IGDD"  # Your Read API Key
THINGSPEAK_CHANNEL_ID = "2845035"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

PUMP_STATUS_FILE = "pump_status.json"

# Ensure the file exists with default OFF (0)
if not os.path.exists(PUMP_STATUS_FILE):
    with open(PUMP_STATUS_FILE, "w") as f:
        json.dump({"pump": 0}, f)

# Function to read pump status from file
def read_pump_status():
    try:
        with open(PUMP_STATUS_FILE, "r") as f:
            return json.load(f)["pump"]
    except (FileNotFoundError, json.JSONDecodeError):
        return 0  # Default to OFF if there's an error

# Function to update pump status in file
def write_pump_status(status):
    with open(PUMP_STATUS_FILE, "w") as f:
        json.dump({"pump": status}, f)
    print(f"✅ Updated pump_status.json: {status}")  # Debugging Log

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    response = requests.get(THINGSPEAK_URL, params={"api_key": THINGSPEAK_READ_API, "results": 1})

    if response.status_code == 200:
        data = response.json()["feeds"][0]

        return jsonify({
            "soil_moisture": data.get("field1", "N/A"),
            "temperature": data.get("field2", "N/A"),
            "humidity": data.get("field3", "N/A"),
            "irrigation": "ON" if data.get("field4") == "1" else "OFF"
        })
    else:
        print("❌ Error fetching ThingSpeak data:", response.text)
        return jsonify({
            "soil_moisture": "N/A",
            "temperature": "N/A",
            "humidity": "N/A",
            "irrigation": "ERROR"
        }), 500


@app.route("/api/control_pump", methods=["POST"])
def control_pump():
    action = request.json.get("action")  # "on" or "off"
    pump_status = 1 if action == "on" else 0  # Convert to 1 or 0

    # ✅ Store pump status in JSON file
    write_pump_status(pump_status)

    # ✅ Send pump status to ThingSpeak (Field 4)
    response = requests.get("https://api.thingspeak.com/update", params={
        "api_key": THINGSPEAK_WRITE_API,
        "field4": pump_status
    })

    if response.status_code == 200 and response.text.strip().isdigit():
        print(f"✅ Pump turned {action}, ThingSpeak entry: {response.text}")
        return jsonify({"message": f"Pump turned {action}", "status": pump_status})
    else:
        print(f"❌ Error updating ThingSpeak: {response.text}")
        return jsonify({"error": "Failed to update ThingSpeak"}), 500

if __name__ == "__main__":
    app.run(debug=True)
