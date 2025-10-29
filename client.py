#!/usr/bin/env python3
"""
client.py
Client that polls api.py endpoint and controls buzzer/LCD based on temperature and humidity thresholds
Merged functionality from watch.py - now supports optional LCD display
Also controls LED indicators for heat/pump devices
"""
import time
import requests
import json
import atexit
import argparse
import os
from gpiozero import Buzzer
from common import (
    READ_INTERVAL,
    TEMP_HIGH_THRESHOLD,
    TEMP_LOW_THRESHOLD,
    HUMIDITY_LOW_THRESHOLD,
    HUMIDITY_HIGH_THRESHOLD,
    API_SERVER_IP,
    API_PORT,
    BUZZ_INTERVAL,
    ERROR_DISPLAY_INTERVAL,
    check_alert,
    DEVICES,
    setup_logging,
    BUZZER_GPIO_PIN,
    LCD_I2C_ADDRESS,
    LCD_LINE_LENGTH,
    BUZZ_DURATION_SECONDS,
    ALERT_DISPLAY_DURATION_SECONDS
)

parser = argparse.ArgumentParser(description='Hermie Client Monitor')
parser.add_argument('--headless', action='store_true',
                    help='Run in headless mode (no LCD/LEDs)')
args = parser.parse_args()

HEADLESS_MODE = args.headless or os.getenv("HEADLESS", "false").lower() == "true"
logger = setup_logging()

# Initialize LCD - only if not headless (will crash if LCD missing)
lcd = None
if not HEADLESS_MODE:
    from RPLCD.i2c import CharLCD
    logger.info("Initializing LCD...")
    lcd = CharLCD('PCF8574', LCD_I2C_ADDRESS)
    logger.info("LCD initialized successfully!")

# Initialize LED indicators - only if not headless (will crash if LEDs missing)
leds_available = False
led_gpio = None
if not HEADLESS_MODE:
    import RPi.GPIO as LED_GPIO
    led_gpio = LED_GPIO
    logger.info("Initializing LED indicators...")
    led_gpio.setmode(LED_GPIO.BCM)
    for device_name, pins in DEVICES.items():
        led_pin = pins["led"]
        led_gpio.setup(led_pin, LED_GPIO.OUT)
        led_gpio.output(led_pin, LED_GPIO.LOW)
        logger.info(f"LED initialized: {device_name.title()} on GPIO {led_pin}")
    leds_available = True
    logger.info("LED indicators initialized successfully!")

# Cleanup LEDs on exit
def cleanup_leds():
    if leds_available and led_gpio:
        led_gpio.cleanup()

atexit.register(cleanup_leds)

# CONFIG
API_URL = f"http://{API_SERVER_IP}:{API_PORT}/sensor"
POLL_INTERVAL = READ_INTERVAL  # Use same interval as other scripts
BUZZ_DURATION = BUZZ_DURATION_SECONDS  # Use constant
BUZZ_COOLDOWN = BUZZ_INTERVAL  # 5 minutes between buzzes (from common.py)

# Initialize buzzer
logger.info(f"Initializing buzzer on GPIO {BUZZER_GPIO_PIN}...")
buzzer = Buzzer(BUZZER_GPIO_PIN)
logger.info("Buzzer initialized successfully!")

# Track last buzz time
last_buzz_time = 0

# Track last error display time (for LCD)
last_error_display_time = 0

# Track last log time (same interval as buzzer cooldown)
last_log_time = 0

def get_sensor_data():
    """Fetch sensor data from API endpoint"""
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ERROR fetching from API: {e}")
        return None

def display_on_lcd(line1, line2=None):
    """Display text on LCD - unified function for all display needs"""
    if lcd is None:
        return
    lcd.clear()
    lcd.write_string(str(line1)[:LCD_LINE_LENGTH])
    if line2:
        lcd.crlf()
        lcd.write_string(str(line2)[:LCD_LINE_LENGTH])

def update_leds(sensor_data):
    """Update LED indicators based on device state from API"""
    if not leds_available or led_gpio is None:
        return

    for device_name, pins in DEVICES.items():
        state_key = f"{device_name}_on"
        device_on = sensor_data.get(state_key, False)
        led_pin = pins["led"]

        if device_on:
            led_gpio.output(led_pin, led_gpio.HIGH)
        else:
            led_gpio.output(led_pin, led_gpio.LOW)

def should_buzz(alert_triggered, alert_message, current_time):
    """Determine if buzzer should sound based on alerts and cooldown"""
    if not alert_triggered:
        return False

    time_since_last_buzz = current_time - last_buzz_time
    if time_since_last_buzz >= BUZZ_COOLDOWN:
        return True
    else:
        cooldown_remaining = BUZZ_COOLDOWN - time_since_last_buzz
        logger.info(f"Alert condition present but buzzer on cooldown ({cooldown_remaining:.0f}s remaining)")
        return False

def log_status(sensor_data, alert_triggered, buzzer_active):
    """Log sensor data and system status concisely"""
    status = {
        "sensor": sensor_data,
        "lcd": lcd is not None,
        "alert": alert_triggered,
        "buzzer": buzzer_active
    }
    logger.info(f"[STATUS] {json.dumps(status, separators=(',', ':'))}")

def main():
    global last_buzz_time, last_error_display_time, last_log_time

    logger.info("Starting client.py")
    logger.info(f"Mode: {'HEADLESS' if HEADLESS_MODE else 'DISPLAY'}")
    logger.info(f"Polling {API_URL} every {POLL_INTERVAL} seconds")
    logger.info(f"Temperature thresholds: {TEMP_LOW_THRESHOLD}F - {TEMP_HIGH_THRESHOLD}F")
    logger.info(f"Humidity thresholds: {HUMIDITY_LOW_THRESHOLD}% - {HUMIDITY_HIGH_THRESHOLD}%")
    logger.info(f"Buzzer cooldown: {BUZZ_COOLDOWN} seconds")
    if not HEADLESS_MODE:
        logger.info(f"LCD available: {lcd is not None}")
        logger.info(f"LED indicators available: {leds_available}")
    logger.info(f"Logging interval: {BUZZ_COOLDOWN} seconds (same as buzzer cooldown)")
    logger.info("-" * 50)

    while True:
        current_time = time.time()

        # Fetch sensor data from API
        data = get_sensor_data()

        if data is None:
            logger.warning("Failed to get sensor data, will retry next interval")
            if lcd and current_time - last_error_display_time >= ERROR_DISPLAY_INTERVAL:
                display_on_lcd("API Unavailable")
                last_error_display_time = current_time
        else:
            # Extract values from response
            temp_f = data.get("temperature_f")
            humidity = data.get("humidity")
            error = data.get("error")
            alert = data.get("alert")

            # Display current readings
            if temp_f is not None:
                logger.debug(f"Temperature: {temp_f:.1f}F")
            if humidity is not None:
                logger.debug(f"Humidity: {humidity:.1f}%")
            if error:
                logger.error(f"API Error: {error}")
                if lcd and current_time - last_error_display_time >= ERROR_DISPLAY_INTERVAL:
                    error_str = str(error)
                    display_on_lcd(error_str[:LCD_LINE_LENGTH], error_str[LCD_LINE_LENGTH:LCD_LINE_LENGTH*2] if len(error_str) > LCD_LINE_LENGTH else None)
                    last_error_display_time = current_time
            if alert:
                logger.warning(f"API Alert: {alert}")

            # Check thresholds
            alert_triggered, alert_message, lcd_alert = check_alert(temp_f, humidity)
            if alert_triggered:
                logger.warning(f"ALERT: {alert_message}")

            # Check if we should buzz
            buzzer_active = False
            if should_buzz(alert_triggered, alert_message, current_time):
                logger.warning("Buzzing for threshold violation...")
                buzzer_active = True

                if lcd and temp_f is not None and humidity is not None:
                    display_on_lcd(lcd_alert, f'{temp_f:.1f}F {humidity:.1f}%')

                buzzer.on()
                time.sleep(BUZZ_DURATION)
                buzzer.off()

                if lcd:
                    time.sleep(ALERT_DISPLAY_DURATION_SECONDS)

                last_buzz_time = current_time
                logger.info(f"Buzzer sounded for {BUZZ_DURATION} second(s)")
            else:
                if temp_f is not None and humidity is not None:
                    display_on_lcd(f'Temp: {temp_f:.1f}F', f'Humidity: {humidity:.1f}%')

            # Update LED indicators based on device state
            update_leds(data)

            # Periodic logging (same interval as buzzer cooldown)
            if current_time - last_log_time >= BUZZ_COOLDOWN:
                log_status(data, alert_triggered, buzzer_active)
                last_log_time = current_time

        # Wait before next poll
        logger.debug(f"Waiting {POLL_INTERVAL} seconds until next poll...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nShutting down client.py...")
        buzzer.off()
        if lcd:
            lcd.clear()
        logger.info("Goodbye!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        buzzer.off()
        if lcd:
            lcd.clear()
        raise