from flask import Flask, render_template, jsonify, request
import requests
import json

app = Flask(__name__)

# ThingSpeak API Keys
THINGSPEAK_WRITE_API = "P1E6IR6D62KSYNAD"
THINGSPEAK_READ_API = "YN19K3YFAH13IGDD"
THINGSPEAK_CHANNEL_ID = "2845035"

# Store the latest pump status in a local file for ESP32 simulation
PUMP_STATUS_FILE = "pump_status.json"

# Ensure the file exists
try:
    with open(PUMP_STATUS_FILE, "r") as f:
        pump_status = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    with open(PUMP_STATUS_FILE, "w") as f:
        json.dump({"pump": 0}, f)  # Default to OFF


# Function to update local pump status
def write_pump_status(status):
    with open(PUMP_STATUS_FILE, "w") as f:
        json.dump({"pump": status}, f)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    # Fetch latest sensor & pump data from ThingSpeak
    response = requests.get(
        f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json",
        params={"api_key": THINGSPEAK_READ_API, "results": 1}
    )

    if response.status_code == 200:
        feed = response.json().get("feeds", [{}])[0]

        # Extract values (fallback to "N/A" if missing)
        return jsonify({
            "soil_moisture": feed.get("field1", "N/A"),
            "temperature": feed.get("field2", "N/A"),
            "humidity": feed.get("field3", "N/A"),
            "irrigation": "ON" if feed.get("field4") == "1" else "OFF"
        })

    return jsonify({"error": "Failed to fetch data"}), 500


@app.route("/api/control_pump", methods=["POST"])
def control_pump():
    action = request.json.get("action")
    pump_status = 1 if action == "on" else 0

    # ✅ Update pump status locally
    write_pump_status(pump_status)

    # ✅ Send pump status to ThingSpeak Field 4
    response = requests.get(
        "https://api.thingspeak.com/update",
        params={"api_key": THINGSPEAK_WRITE_API, "field4": pump_status}
    )

    if response.status_code == 200:
        return jsonify({"message": f"Pump turned {action}"})
    return jsonify({"error": "ThingSpeak update failed"}), 500


if __name__ == "__main__":
    app.run(debug=True)







