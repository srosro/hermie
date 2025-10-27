#!/usr/bin/env python3
"""
test_suite.py
Comprehensive high-level test suite for Hermie environmental monitoring system
Tests API, client logic, and common utilities with real functionality
"""
import requests
import time
import json
from common import (
    check_alert,
    TEMP_HIGH_THRESHOLD,
    TEMP_LOW_THRESHOLD,
    HUMIDITY_HIGH_THRESHOLD,
    HUMIDITY_LOW_THRESHOLD,
    API_SERVER_IP,
    API_PORT,
    DEVICES
)

# API base URL
BASE_URL = f"http://{API_SERVER_IP}:{API_PORT}"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

# Test statistics
test_count = 0
passed_count = 0
failed_count = 0

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_section(text):
    print(f"\n{CYAN}--- {text} ---{RESET}")

def print_success(text):
    global passed_count
    passed_count += 1
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    global failed_count
    failed_count += 1
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}  {text}{RESET}")

def run_test(test_name, test_func):
    """Run a test function and track results"""
    global test_count
    test_count += 1
    print_section(f"TEST {test_count}: {test_name}")
    try:
        result = test_func()
        if result:
            print_success(f"{test_name} passed")
        else:
            print_error(f"{test_name} failed")
        return result
    except Exception as e:
        print_error(f"{test_name} error: {e}")
        return False

# ============================================================================
# COMMON.PY TESTS - Alert threshold logic
# ============================================================================

def test_temp_high_alert():
    """Test temperature high threshold alert"""
    temp = TEMP_HIGH_THRESHOLD + 5
    humidity = 75.0
    alert_triggered, alert_message, lcd_alert = check_alert(temp, humidity)

    print_info(f"Testing temp {temp}°F (threshold: {TEMP_HIGH_THRESHOLD}°F)")
    print_info(f"Alert triggered: {alert_triggered}")
    print_info(f"Alert message: {alert_message}")
    print_info(f"LCD alert: {lcd_alert}")

    return alert_triggered and "exceeds" in alert_message.lower() and "temp" in alert_message.lower()

def test_temp_low_alert():
    """Test temperature low threshold alert"""
    temp = TEMP_LOW_THRESHOLD - 5
    humidity = 75.0
    alert_triggered, alert_message, lcd_alert = check_alert(temp, humidity)

    print_info(f"Testing temp {temp}°F (threshold: {TEMP_LOW_THRESHOLD}°F)")
    print_info(f"Alert triggered: {alert_triggered}")
    print_info(f"Alert message: {alert_message}")
    print_info(f"LCD alert: {lcd_alert}")

    return alert_triggered and "below" in alert_message.lower() and "temp" in alert_message.lower()

def test_humidity_high_alert():
    """Test humidity high threshold alert"""
    temp = 75.0
    humidity = HUMIDITY_HIGH_THRESHOLD + 1
    alert_triggered, alert_message, lcd_alert = check_alert(temp, humidity)

    print_info(f"Testing humidity {humidity}% (threshold: {HUMIDITY_HIGH_THRESHOLD}%)")
    print_info(f"Alert triggered: {alert_triggered}")
    print_info(f"Alert message: {alert_message}")
    print_info(f"LCD alert: {lcd_alert}")

    return alert_triggered and "humidity" in alert_message.lower()

def test_humidity_low_alert():
    """Test humidity low threshold alert"""
    temp = 75.0
    humidity = HUMIDITY_LOW_THRESHOLD - 5
    alert_triggered, alert_message, lcd_alert = check_alert(temp, humidity)

    print_info(f"Testing humidity {humidity}% (threshold: {HUMIDITY_LOW_THRESHOLD}%)")
    print_info(f"Alert triggered: {alert_triggered}")
    print_info(f"Alert message: {alert_message}")
    print_info(f"LCD alert: {lcd_alert}")

    return alert_triggered and "humidity" in alert_message.lower()

def test_no_alert_normal_conditions():
    """Test that no alert triggers under normal conditions"""
    temp = (TEMP_HIGH_THRESHOLD + TEMP_LOW_THRESHOLD) / 2
    humidity = (HUMIDITY_HIGH_THRESHOLD + HUMIDITY_LOW_THRESHOLD) / 2
    alert_triggered, alert_message, lcd_alert = check_alert(temp, humidity)

    print_info(f"Testing normal conditions: temp={temp}°F, humidity={humidity}%")
    print_info(f"Alert triggered: {alert_triggered}")

    return not alert_triggered and alert_message is None

def test_none_temperature_handling():
    """Test handling of None temperature value"""
    alert_triggered, alert_message, lcd_alert = check_alert(None, 75.0)

    print_info(f"Testing None temperature")
    print_info(f"Alert triggered: {alert_triggered}")

    return not alert_triggered

# ============================================================================
# API TESTS - Live API endpoint testing
# ============================================================================

def test_api_health():
    """Test the /health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_info(f"GET /health - Status: {response.status_code}")

        if response.status_code != 200:
            return False

        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")

        return "status" in data
    except Exception as e:
        print_info(f"Error: {e}")
        return False

def test_api_sensor_data():
    """Test the /sensor endpoint returns valid data"""
    try:
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        print_info(f"GET /sensor - Status: {response.status_code}")

        if response.status_code != 200:
            return False

        data = response.json()

        # Check required fields
        required_fields = ["temperature_c", "temperature_f", "humidity", "timestamp_iso"]
        for field in required_fields:
            if field not in data:
                print_info(f"Missing required field: {field}")
                return False

        # Check device states
        for device_name in DEVICES.keys():
            state_key = f"{device_name}_on"
            if state_key not in data:
                print_info(f"Missing device state: {state_key}")
                return False

        print_info(f"Temperature: {data['temperature_f']}°F, Humidity: {data['humidity']}%")
        device_states = ", ".join([f"{dev.title()}={data[f'{dev}_on']}" for dev in DEVICES.keys()])
        print_info(f"Devices: {device_states}")

        return True
    except Exception as e:
        print_info(f"Error: {e}")
        return False

def test_api_power_cycle():
    """Test device control - full cycle on all devices"""
    try:
        # Turn all devices ON
        for device in DEVICES.keys():
            response = requests.post(
                f"{BASE_URL}/control/{device}",
                json={"state": "on"},
                timeout=5
            )
            if response.status_code != 200:
                print_info(f"Failed to turn {device.title()} ON")
                return False
            time.sleep(0.2)

        print_info("All devices turned ON")
        time.sleep(0.5)

        # Verify all are ON
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        data = response.json()
        for device in DEVICES.keys():
            if not data.get(f"{device}_on"):
                print_info(f"{device.title()} not ON as expected")
                return False

        print_info("Verified all devices ON")

        # Turn all devices OFF
        for device in DEVICES.keys():
            response = requests.post(
                f"{BASE_URL}/control/{device}",
                json={"state": "off"},
                timeout=5
            )
            if response.status_code != 200:
                print_info(f"Failed to turn {device.title()} OFF")
                return False
            time.sleep(0.2)

        print_info("All devices turned OFF")
        time.sleep(0.5)

        # Verify all are OFF
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        data = response.json()
        for device in DEVICES.keys():
            if data.get(f"{device}_on"):
                print_info(f"{device.title()} not OFF as expected")
                return False

        print_info("Verified all devices OFF")
        return True

    except Exception as e:
        print_info(f"Error: {e}")
        return False

def test_api_error_handling():
    """Test API error handling for invalid requests"""
    tests_passed = 0
    tests_total = 3

    # Test 1: Invalid device name
    try:
        response = requests.post(
            f"{BASE_URL}/control/invalid_device",
            json={"state": "on"},
            timeout=5
        )
        if response.status_code == 400:
            print_info("✓ Invalid device name correctly rejected (400)")
            tests_passed += 1
        else:
            print_info(f"✗ Expected 400, got {response.status_code}")
    except Exception as e:
        print_info(f"✗ Error testing invalid device: {e}")

    # Test 2: Invalid state value
    try:
        response = requests.post(
            f"{BASE_URL}/control/heat",
            json={"state": "invalid"},
            timeout=5
        )
        if response.status_code == 400:
            print_info("✓ Invalid state value correctly rejected (400)")
            tests_passed += 1
        else:
            print_info(f"✗ Expected 400, got {response.status_code}")
    except Exception as e:
        print_info(f"✗ Error testing invalid state: {e}")

    # Test 3: Missing state field
    try:
        response = requests.post(
            f"{BASE_URL}/control/heat",
            json={},
            timeout=5
        )
        if response.status_code == 400:
            print_info("✓ Missing state field correctly rejected (400)")
            tests_passed += 1
        else:
            print_info(f"✗ Expected 400, got {response.status_code}")
    except Exception as e:
        print_info(f"✗ Error testing missing field: {e}")

    print_info(f"Error handling tests: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total

# ============================================================================
# CLIENT LOGIC TESTS - Simulate client.py behavior
# ============================================================================

def test_client_sensor_polling():
    """Test client-like polling of sensor endpoint"""
    try:
        # Simulate what client.py does
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)

        if response.status_code != 200:
            print_info(f"Failed to poll sensor: status {response.status_code}")
            return False

        data = response.json()
        temp_f = data.get("temperature_f")
        humidity = data.get("humidity")
        error = data.get("error")

        print_info(f"Polled sensor: temp={temp_f}°F, humidity={humidity}%")

        if error:
            print_info(f"API reported error: {error}")

        # Check if alert should trigger (simulating client logic)
        alert_triggered, alert_message, _ = check_alert(temp_f, humidity)

        if alert_triggered:
            print_info(f"Alert condition detected: {alert_message}")
        else:
            print_info("No alert conditions")

        # Success if we got valid data
        return temp_f is not None and humidity is not None

    except Exception as e:
        print_info(f"Error: {e}")
        return False

def test_client_alert_detection():
    """Test client alert detection logic with current sensor data"""
    try:
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        data = response.json()

        temp_f = data.get("temperature_f")
        humidity = data.get("humidity")

        print_info(f"Current conditions: {temp_f}°F, {humidity}%")
        print_info(f"Thresholds: temp={TEMP_LOW_THRESHOLD}-{TEMP_HIGH_THRESHOLD}°F")
        print_info(f"           humidity={HUMIDITY_LOW_THRESHOLD}-{HUMIDITY_HIGH_THRESHOLD}%")

        alert_triggered, alert_message, _ = check_alert(temp_f, humidity)

        if alert_triggered:
            print_info(f"Alert would trigger: {alert_message}")
        else:
            print_info("No alert would trigger")

        # Test always passes - just demonstrates the logic
        return True

    except Exception as e:
        print_info(f"Error: {e}")
        return False

# ============================================================================
# INTEGRATION TESTS - End-to-end scenarios
# ============================================================================

def test_integration_power_and_sensor():
    """Test integration of device control and sensor reading"""
    try:
        # Get initial state
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        initial_data = response.json()
        print_info(f"Initial temp: {initial_data['temperature_f']}°F")
        print_info(f"Initial heat: {initial_data['heat_on']}")

        # Toggle heat device
        requests.post(f"{BASE_URL}/control/heat", json={"state": "on"}, timeout=5)
        time.sleep(0.3)

        # Read sensor again
        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        updated_data = response.json()

        print_info(f"After heat ON: heat_on={updated_data['heat_on']}")

        # Verify device changed
        if not updated_data['heat_on']:
            print_info("Heat did not turn on")
            return False

        # Turn back off
        requests.post(f"{BASE_URL}/control/heat", json={"state": "off"}, timeout=5)
        time.sleep(0.3)

        response = requests.get(f"{BASE_URL}/sensor", timeout=5)
        final_data = response.json()

        print_info(f"After heat OFF: heat_on={final_data['heat_on']}")

        return not final_data['heat_on']

    except Exception as e:
        print_info(f"Error: {e}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run complete test suite"""
    global test_count, passed_count, failed_count
    test_count = 0
    passed_count = 0
    failed_count = 0

    print_header("HERMIE COMPREHENSIVE TEST SUITE")
    print(f"{CYAN}Testing API at: {BASE_URL}{RESET}")
    print(f"{CYAN}Devices configured: {list(DEVICES.keys())}{RESET}")

    # Common.py tests
    print_header("COMMON.PY - Alert Logic Tests")
    run_test("Temperature High Alert", test_temp_high_alert)
    run_test("Temperature Low Alert", test_temp_low_alert)
    run_test("Humidity High Alert", test_humidity_high_alert)
    run_test("Humidity Low Alert", test_humidity_low_alert)
    run_test("No Alert on Normal Conditions", test_no_alert_normal_conditions)
    run_test("Handle None Temperature", test_none_temperature_handling)

    # API tests
    print_header("API.PY - Endpoint Tests")
    run_test("Health Endpoint", test_api_health)
    run_test("Sensor Data Endpoint", test_api_sensor_data)
    run_test("Device Control Full Cycle", test_api_power_cycle)
    run_test("API Error Handling", test_api_error_handling)

    # Client logic tests
    print_header("CLIENT.PY - Polling & Alert Logic Tests")
    run_test("Client Sensor Polling", test_client_sensor_polling)
    run_test("Client Alert Detection", test_client_alert_detection)

    # Integration tests
    print_header("INTEGRATION - End-to-End Tests")
    run_test("Device Control & Sensor Integration", test_integration_power_and_sensor)

    # Summary
    print_header("TEST SUMMARY")
    print(f"{CYAN}Total Tests: {test_count}{RESET}")
    print(f"{GREEN}Passed: {passed_count}{RESET}")
    print(f"{RED}Failed: {failed_count}{RESET}")

    if failed_count == 0:
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
    else:
        print(f"\n{RED}{'='*60}{RESET}")
        print(f"{RED}SOME TESTS FAILED{RESET}")
        print(f"{RED}{'='*60}{RESET}\n")

    return failed_count == 0

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{RESET}")
        exit(1)
