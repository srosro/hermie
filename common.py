"""
common.py
Shared configuration and utilities for Hermie environmental monitoring system
"""

# API Server Configuration
API_SERVER_IP = "100.101.120.3"  # Tailscale IP of the Raspberry Pi server
API_PORT = 5000

# Sensor reading interval
READ_INTERVAL = 15  # seconds between sensor reads

# Temperature calibration
TEMP_OFFSET_F = -2.0  # temperature offset in Fahrenheit

# Temperature thresholds
TEMP_HIGH_THRESHOLD = 85.0  # degrees F
TEMP_LOW_THRESHOLD = 70.0   # degrees F

# Humidity thresholds
HUMIDITY_LOW_THRESHOLD = 65.0  # percent
HUMIDITY_HIGH_THRESHOLD = 99.97  # percent

# Watch-specific intervals
BUZZ_INTERVAL = 1200  # 20 minutes in seconds
ERROR_DISPLAY_INTERVAL = 20  # seconds between error displays on LCD

# Power outlet GPIO pin configuration
# Using BCM numbering
POWER_OUTLETS = {
    1: 17,  # GPIO 17 (physical pin 11)
    2: 27,  # GPIO 27 (physical pin 13)
    3: 22,  # GPIO 22 (physical pin 15)
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
