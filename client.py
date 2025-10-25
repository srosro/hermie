#!/usr/bin/env python3
"""
client.py
Client that polls api.py endpoint and controls buzzer based on temperature and humidity thresholds
"""
import time
import requests
from gpiozero import Buzzer
from datetime import datetime
from common import (
    READ_INTERVAL,
    TEMP_HIGH_THRESHOLD,
    TEMP_LOW_THRESHOLD,
    HUMIDITY_LOW_THRESHOLD,
    HUMIDITY_HIGH_THRESHOLD,
    API_SERVER_IP,
    API_PORT,
    check_alert
)

# CONFIG
API_URL = f"http://{API_SERVER_IP}:{API_PORT}/sensor"
POLL_INTERVAL = READ_INTERVAL  # Use same interval as other scripts
BUZZ_DURATION = 1  # seconds to buzz
BUZZ_COOLDOWN = 300  # 5 minutes between buzzes to avoid constant alerting

# Initialize buzzer on GPIO 16 (same pin as hermie_watch.py)
print("Initializing buzzer on GPIO 16...")
buzzer = Buzzer(16)
print("Buzzer initialized successfully!")

# Track last buzz time
last_buzz_time = 0

def get_sensor_data():
    """Fetch sensor data from API endpoint"""
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching from API: {e}")
        return None

def should_buzz(alert_triggered, alert_message, current_time):
    """Determine if buzzer should sound based on alerts and cooldown"""
    if not alert_triggered:
        return False
    
    time_since_last_buzz = current_time - last_buzz_time
    if time_since_last_buzz >= BUZZ_COOLDOWN:
        return True
    else:
        cooldown_remaining = BUZZ_COOLDOWN - time_since_last_buzz
        print(f"Alert condition present but buzzer on cooldown ({cooldown_remaining:.0f}s remaining)")
        return False

def main():
    global last_buzz_time
    
    print(f"Starting client.py")
    print(f"Polling {API_URL} every {POLL_INTERVAL} seconds")
    print(f"Temperature thresholds: {TEMP_LOW_THRESHOLD}F - {TEMP_HIGH_THRESHOLD}F")
    print(f"Humidity thresholds: {HUMIDITY_LOW_THRESHOLD}% - {HUMIDITY_HIGH_THRESHOLD}%")
    print(f"Buzzer cooldown: {BUZZ_COOLDOWN} seconds")
    print("-" * 50)
    
    iteration = 0
    while True:
        iteration += 1
        current_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n[{timestamp}] Poll #{iteration}")
        
        # Fetch sensor data from API
        data = get_sensor_data()
        
        if data is None:
            print("Failed to get sensor data, will retry next interval")
        else:
            # Extract values from response
            temp_f = data.get("temperature_f")
            humidity = data.get("humidity")
            error = data.get("error")
            alert = data.get("alert")
            
            # Display current readings
            if temp_f is not None:
                print(f"Temperature: {temp_f:.1f}F")
            if humidity is not None:
                print(f"Humidity: {humidity:.1f}%")
            if error:
                print(f"API Error: {error}")
            if alert:
                print(f"API Alert: {alert}")
            
            # Check thresholds
            alert_triggered, alert_message, _ = check_alert(temp_f, humidity)
            if alert_triggered:
                print(f"ALERT: {alert_message}")
            
            # Check if we should buzz
            if should_buzz(alert_triggered, alert_message, current_time):
                print(f"Buzzing for threshold violation...")
                buzzer.on()
                time.sleep(BUZZ_DURATION)
                buzzer.off()
                last_buzz_time = current_time
                print(f"Buzzer sounded for {BUZZ_DURATION} second(s)")
        
        # Wait before next poll
        print(f"Waiting {POLL_INTERVAL} seconds until next poll...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down client.py...")
        buzzer.off()
        print("Buzzer turned off. Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        buzzer.off()
        raise