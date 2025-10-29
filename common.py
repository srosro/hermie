"""
common.py
Shared configuration and utilities for Hermie environmental monitoring system
"""
import logging

# API Server Configuration
API_SERVER_IP = "100.101.120.3"  # Tailscale IP of the Raspberry Pi server
API_PORT = 5000

# Hardware Configuration
BUZZER_GPIO_PIN = 16
LCD_I2C_ADDRESS = 0x27
LCD_LINE_LENGTH = 16
BUZZ_DURATION_SECONDS = 3
ALERT_DISPLAY_DURATION_SECONDS = 20

# Sensor reading interval
READ_INTERVAL = 5  # seconds between sensor reads

# Temperature calibration
TEMP_OFFSET_F = -1.0  # temperature offset in Fahrenheit

# Temperature thresholds
TEMP_HIGH_THRESHOLD = 85.0  # degrees F
TEMP_LOW_THRESHOLD = 75.0   # degrees F

# Humidity thresholds
HUMIDITY_LOW_THRESHOLD = 75.0  # percent
HUMIDITY_HIGH_THRESHOLD = 95.0  # percent

# Notification cooldown interval for buzzes, LCD alerts, and logging
NOTIF_COOLDOWN = 300  # 5 minutes in seconds

# Device control GPIO pin configuration
# Using BCM numbering
DEVICES = {
    "heat": {
        "led": 17,    # GPIO 17 (physical pin 11) - LED indicator
        "relay": 27,  # GPIO 27 (physical pin 13) - IoT Power Relay
    },
    "pump": {
        "led": 22,    # GPIO 22 (physical pin 15) - LED indicator
        "relay": 23,  # GPIO 23 (physical pin 16) - Pump relay
    }
}

def check_alert(temp_f, humidity):
    """
    Check if temperature or humidity values exceed thresholds.
    Returns tuple of (alert_triggered, alert_message, lcd_alert)
    lcd_alert is a 16-char string for LCD display
    """
    if temp_f is None:
        return (False, None, None)
    
    if temp_f > TEMP_HIGH_THRESHOLD:
        return (True, 
                f"Temperature {temp_f:.1f}F exceeds {TEMP_HIGH_THRESHOLD}F",
                "Alert: High temp")
    
    if temp_f < TEMP_LOW_THRESHOLD:
        return (True,
                f"Temperature {temp_f:.1f}F below {TEMP_LOW_THRESHOLD}F",
                "Alert: Low temp")
    
    if humidity is not None:
        if humidity > HUMIDITY_HIGH_THRESHOLD:
            return (True,
                    f"Humidity {humidity:.1f}% exceeds {HUMIDITY_HIGH_THRESHOLD}%",
                    "Alert: High hum")
        if humidity < HUMIDITY_LOW_THRESHOLD:
            return (True,
                    f"Humidity {humidity:.1f}% below {HUMIDITY_LOW_THRESHOLD}%",
                    "Alert: Low humid")

    return (False, None, None)

def setup_logging():
    """Configure logging with consistent format across all scripts"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)
