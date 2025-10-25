from RPLCD.i2c import CharLCD
import adafruit_sht31d
import board
import time
from gpiozero import Buzzer
from common import (
    READ_INTERVAL,
    TEMP_OFFSET_F,
    BUZZ_INTERVAL,
    ERROR_DISPLAY_INTERVAL,
    check_alert
)

print("Initializing LCD...")
# Initialize LCD
lcd = CharLCD('PCF8574', 0x27)
print("LCD initialized successfully!")

print("Initializing buzzer on GPIO 16...")
buzzer = Buzzer(16)
print("Buzzer initialized successfully!")

print("Initializing SHT30 sensor on I2C (GPIO 2=SDA, GPIO 3=SCL)...")
# Initialize SHT30 on default I2C pins
i2c = board.I2C()  # Uses GPIO 2 (SDA) and GPIO 3 (SCL)
sht30_device = adafruit_sht31d.SHT31D(i2c)
print("SHT30 initialized successfully!")

# Give the sensor a moment to stabilize
print("Waiting for sensor to stabilize...")
time.sleep(2)

# Do a test read to make sure it's working
try:
    test_temp = sht30_device.temperature
    test_humidity = sht30_device.relative_humidity
    print(f"Sensor ready! Initial reading: {test_temp:.1f}°C, {test_humidity:.1f}%")
except Exception as e:
    print(f"Warning: Initial sensor read failed: {e}")
    print("Waiting 3 more seconds and trying again...")
    time.sleep(3)

# Track last buzz time
last_buzz_time = 0

# Track last error display time
last_error_display_time = 0

try:
    iteration = 0
    while True:
        iteration += 1
        print(f"\n--- Reading #{iteration} ---")
        try:
            # Read temperature and humidity with retry logic
            print("Reading temperature and humidity...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    temperature_c = sht30_device.temperature
                    humidity = sht30_device.relative_humidity
                    break  # Success, exit retry loop
                except OSError as e:
                    if attempt < max_retries - 1:
                        print(f"Read attempt {attempt + 1} failed, retrying in 1 second...")
                        time.sleep(1)
                    else:
                        raise  # Re-raise if all retries failed
            
            print(f"Temperature (C): {temperature_c:.2f}")

            temperature_f = (temperature_c * 9/5 + 32) + TEMP_OFFSET_F
            print(f"Temperature (F): {temperature_f:.1f}")
            print(f"Humidity: {humidity:.1f}%")

            # Clear display
            print("Updating LCD...")
            lcd.clear()

            # Display on LCD
            lcd.write_string(f'Temp: {temperature_f:.1f}F')
            lcd.crlf()  # Move to second line
            lcd.write_string(f'Humidity: {humidity:.1f}%')
            print("LCD updated successfully!")

            # Check if we should buzz
            current_time = time.time()
            alert_triggered, alert_message, lcd_alert = check_alert(temperature_f, humidity)

            if alert_triggered:
                if current_time - last_buzz_time >= BUZZ_INTERVAL:
                    print(f"ALERT: {alert_message} Buzzing...")

                    # Show alert on LCD
                    lcd.clear()
                    lcd.write_string(lcd_alert)
                    lcd.crlf()
                    lcd.write_string(f'{temperature_f:.1f}F {humidity:.1f}%')

                    # Buzz
                    buzzer.on()
                    time.sleep(1)
                    buzzer.off()

                    # Keep alert displayed for 20 extra seconds
                    time.sleep(20)  # Already waited 1 second during buzz

                    last_buzz_time = current_time
                else:
                    time_until_next = BUZZ_INTERVAL - (current_time - last_buzz_time)
                    print(f"{alert_message} Buzz on cooldown ({time_until_next:.0f}s remaining)")

            # Wait between readings
            print(f"Waiting {READ_INTERVAL} seconds...")
            time.sleep(READ_INTERVAL)

        except (RuntimeError, OSError) as error:
            # SHT30 can occasionally fail to read
            print(f"ERROR reading sensor: {error}")

            # Only display error on LCD if cooldown has elapsed
            current_time = time.time()
            if current_time - last_error_display_time >= ERROR_DISPLAY_INTERVAL:
                # Display error on LCD (first 16 chars per line)
                error_str = str(error)
                lcd.clear()
                lcd.write_string(error_str[:16])  # First 16 chars on line 1
                if len(error_str) > 16:
                    lcd.crlf()
                    lcd.write_string(error_str[16:32])  # Next 16 chars on line 2

                last_error_display_time = current_time
            else:
                time_until_next = ERROR_DISPLAY_INTERVAL - (current_time - last_error_display_time)
                print(f"Error display on cooldown ({time_until_next:.0f}s remaining)")

            print("Waiting 5 seconds before retry...")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")

            # Display unexpected error on LCD (no cooldown for unexpected errors)
            error_str = f"{type(e).__name__}: {str(e)}"
            lcd.clear()
            lcd.write_string(error_str[:16])
            if len(error_str) > 16:
                lcd.crlf()
                lcd.write_string(error_str[16:32])

            raise

except KeyboardInterrupt:
    print("\nExiting...")
    buzzer.off()
    lcd.clear()
    print("Cleanup complete!")
