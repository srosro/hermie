#!/usr/bin/env python3
"""
Simple LED test script
Turns LED on for 5 seconds, then off
"""
import time
import RPi.GPIO as GPIO
from common import DEVICES

gpio_pin = DEVICES["heat"]["led"]
print(f"Testing Heat LED on GPIO {gpio_pin}")

try:
    # Setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_pin, GPIO.OUT)

    print("Turning LED ON...")
    GPIO.output(gpio_pin, GPIO.HIGH)
    time.sleep(5)

    print("Turning LED OFF...")
    GPIO.output(gpio_pin, GPIO.LOW)

    print("Test complete!")

except Exception as e:
    print(f"Error: {e}")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up")
