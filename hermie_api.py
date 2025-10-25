#!/usr/bin/env python3
"""
hermie_api.py
Background thread reads SHT31D sensor and exposes latest reading via Flask at /sensor
"""
import time
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify
import board
import adafruit_sht31d
from constants import (
    READ_INTERVAL,
    TEMP_OFFSET_F,
    TEMP_HIGH_THRESHOLD,
    TEMP_LOW_THRESHOLD,
    HUMIDITY_LOW_THRESHOLD
)

# Shared state
state = {
    "temperature_c": None,
    "temperature_f": None,
    "humidity": None,
    "timestamp_iso": None,
    "error": None,
    "last_read_ok": False,
    "alert": None
}

# Initialize sensor
def init_sensor():
    try:
        i2c = board.I2C()
        sensor = adafruit_sht31d.SHT31D(i2c)
        return sensor
    except Exception as e:
        state["error"] = f"Sensor init failed: {e}"
        return None

def compute_alert(temp_f, humidity):
    if temp_f is None:
        return None
    if temp_f > TEMP_HIGH_THRESHOLD:
        return f"high_temp: {temp_f:.1f}F > {TEMP_HIGH_THRESHOLD}F"
    if temp_f < TEMP_LOW_THRESHOLD:
        return f"low_temp: {temp_f:.1f}F < {TEMP_LOW_THRESHOLD}F"
    if humidity is not None and humidity < HUMIDITY_LOW_THRESHOLD:
        return f"low_humidity: {humidity:.1f}% < {HUMIDITY_LOW_THRESHOLD}%"
    return None

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
    print("Warning: sensor init failed; API will run but return errors until sensor is available.")

reader_thread = threading.Thread(target=reader_loop, args=(sensor,), daemon=True)
reader_thread.start()

# Flask API
app = Flask(__name__)

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

if __name__ == "__main__":
    # Bind to 0.0.0.0 so LAN devices can access
    app.run(host="0.0.0.0", port=5000)
