"""
constants.py
Shared configuration constants for Hermie environmental monitoring system
"""

# Sensor reading interval
READ_INTERVAL = 15  # seconds between sensor reads

# Temperature calibration
TEMP_OFFSET_F = -2.0  # temperature offset in Fahrenheit

# Temperature thresholds
TEMP_HIGH_THRESHOLD = 85.0  # degrees F
TEMP_LOW_THRESHOLD = 70.0   # degrees F

# Humidity thresholds
HUMIDITY_LOW_THRESHOLD = 65.0  # percent

# Watch-specific intervals
BUZZ_INTERVAL = 1200  # 20 minutes in seconds
ERROR_DISPLAY_INTERVAL = 20  # seconds between error displays on LCD
