#!/usr/bin/env python3
"""
api.py
Background thread reads SHT31D sensor and exposes latest reading via Flask at /sensor
"""
import time
import threading
import atexit
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
import board
import adafruit_sht31d
import RPi.GPIO as GPIO
from common import (
    READ_INTERVAL,
    TEMP_OFFSET_F,
    check_alert,
    DEVICES,
    setup_logging
)

logger = setup_logging()

# Shared state
state = {
    "temperature_c": None,
    "temperature_f": None,
    "humidity": None,
    "timestamp_iso": None,
    "error": None,
    "last_read_ok": False,
    "alert": None,
}

# Dynamically add device states
for device_name in DEVICES.keys():
    state[f"{device_name}_on"] = False

# Initialize sensor
def init_sensor():
    try:
        i2c = board.I2C()
        sensor = adafruit_sht31d.SHT31D(i2c)
        return sensor
    except Exception as e:
        state["error"] = f"Sensor init failed: {e}"
        return None

# Initialize GPIO for device control (relays only - LEDs controlled by client.py)
def init_gpio():
    try:
        GPIO.setmode(GPIO.BCM)
        for device_name, pins in DEVICES.items():
            # Only initialize relay pins, not LED pins
            relay_pin = pins["relay"]
            GPIO.setup(relay_pin, GPIO.OUT)
            GPIO.output(relay_pin, GPIO.LOW)
            logger.info(f"GPIO initialized: {device_name.title()} relay on GPIO {relay_pin}")
    except Exception as e:
        logger.error(f"GPIO init failed: {e}")

# Cleanup GPIO on exit
def cleanup_gpio():
    GPIO.cleanup()

atexit.register(cleanup_gpio)

def compute_alert(temp_f, humidity):
    alert_triggered, alert_message, _ = check_alert(temp_f, humidity)
    return alert_message if alert_triggered else None

def reader_loop(sensor):
    while True:
        try:
            # Read with retries like your other script
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    temp_c = sensor.temperature
                    humidity = sensor.relative_humidity
                    break
                except OSError:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        raise
            temp_f = (temp_c * 9.0/5.0) + 32.0 + TEMP_OFFSET_F
            ts = datetime.now(timezone.utc).isoformat()
            state.update({
                "temperature_c": round(temp_c, 2),
                "temperature_f": round(temp_f, 2),
                "humidity": round(humidity, 2),
                "timestamp_iso": ts,
                "error": None,
                "last_read_ok": True,
            })
            state["alert"] = compute_alert(temp_f, humidity)
        except Exception as e:
            # On read error keep previous good reading but record error
            state["error"] = f"read_error: {type(e).__name__}: {e}"
            state["last_read_ok"] = False
        time.sleep(READ_INTERVAL)

# Start sensor and background thread
sensor = init_sensor()
if sensor is None:
    # Still start Flask to allow returning error info
    logger.warning("Sensor init failed; API will run but return errors until sensor is available.")

reader_thread = threading.Thread(target=reader_loop, args=(sensor,), daemon=True)
reader_thread.start()

# Initialize GPIO for device control
init_gpio()

# Flask API
app = Flask(__name__)

# Configure CORS for all endpoints
# Allows cross-origin requests from any origin for all HTTP methods
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.get("/sensor")
def get_sensor():
    """Return latest reading as JSON"""
    # Return entire state
    return jsonify(state)

@app.get("/health")
def health():
    return jsonify({
        "status": "ok" if state.get("last_read_ok") else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.post("/control/<device>")
def set_device(device):
    """Control device relay on/off (LED indicators controlled by client.py)"""
    # Validate device name
    if device not in DEVICES:
        return jsonify({"error": f"Invalid device. Valid devices: {list(DEVICES.keys())}"}), 400

    data = request.get_json()

    if not data or "state" not in data:
        return jsonify({"error": "Missing 'state' field in request body"}), 400

    requested_state = data["state"].lower()

    if requested_state not in ["on", "off"]:
        return jsonify({"error": "State must be 'on' or 'off'"}), 400

    try:
        device_pins = DEVICES[device]
        state_key = f"{device}_on"

        if requested_state == "on":
            # Turn on relay only (LED controlled by client.py)
            GPIO.output(device_pins["relay"], GPIO.HIGH)
            state[state_key] = True
        else:
            # Turn off relay only (LED controlled by client.py)
            GPIO.output(device_pins["relay"], GPIO.LOW)
            state[state_key] = False

        return jsonify({
            "status": "success",
            state_key: state[state_key],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({"error": f"Failed to set {device} state: {e}"}), 500

if __name__ == "__main__":
    # Bind to 0.0.0.0 so LAN devices can access
    app.run(host="0.0.0.0", port=5000)
