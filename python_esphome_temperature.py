from machine import Pin
import network
import time
from umqtt.simple import MQTTClient
import json
import onewire
import ds18x20

# --- HARDWARE DEFINITIONS ---
led = Pin(8, Pin.OUT)
led.value(1)  # Start with LED OFF
data_pin = Pin(10)  # Keyes DS18B20 Signal Pin
ow = onewire.OneWire(data_pin)
ds = ds18x20.DS18X20(ow)

# --- NETWORK CONFIGURATION ---
SSID = "ASUS-MyHome"
PASSWORD = "19621117Carie"
MQTT_BROKER = "192.168.1.122"
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASS = ""

# JUMPING TO V99: This instantly bypasses all stuck, old data in your MQTT broker
CLIENT_ID = "esp32c3_master_final_v99"
DEVICE_NAME = "ESP32-C3 Final Suite"

TOPIC_SWITCH_CONFIG = "homeassistant/switch/esp32c3_v99_sw/config"
TOPIC_SWITCH_STATE  = "homeassistant/switch/esp32c3_v99_sw/state"
TOPIC_SWITCH_CMD    = "homeassistant/switch/esp32c3_v99_sw/set"
TOPIC_TEMP_CONFIG   = "homeassistant/sensor/esp32c3_v99_tp/config"
TOPIC_TEMP_STATE    = "homeassistant/sensor/esp32c3_v99_tp/state"

def mqtt_callback(topic, msg):
    command = msg.decode('utf-8')
    print(f"Home Assistant Command: {command}")
    if command == "ON":
        led.value(0)
        client.publish(TOPIC_SWITCH_STATE, "ON", retain=True)
    elif command == "OFF":
        led.value(1)
        client.publish(TOPIC_SWITCH_STATE, "OFF", retain=True)

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(f"Connecting to Wi-Fi ({SSID})...")
if not wlan.isconnected():
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.5)
print("Wi-Fi Connected! IP:", wlan.ifconfig())

def connect_mqtt():
    global client
    print(f"Connecting to MQTT Broker ({MQTT_BROKER})...")
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASS, keepalive=60)
        client.set_callback(mqtt_callback)
        client.connect(clean_session=True)
        time.sleep(0.2)
        client.subscribe(TOPIC_SWITCH_CMD)
        print("MQTT Connection Successful!")
        
        device_definition = {
            "identifiers": [CLIENT_ID],
            "name": DEVICE_NAME,
            "model": "ESP32-C3 Mini",
            "manufacturer": "MicroPython"
        }

        # 1. Switch Discovery Setup
        switch_payload = {
            "name": "Onboard Light Switch",
            "state_topic": TOPIC_SWITCH_STATE,
            "command_topic": TOPIC_SWITCH_CMD,
            "payload_on": "ON",
            "payload_off": "OFF",
            "unique_id": "esp32c3_v99_switch_entity",
            "device": device_definition
        }

        # 2. Temperature Discovery Setup 
        # BULLETPROOF CHANGE: Removed device_class and unit restrictions entirely. 
        # This makes it a standard text/numeric sensor payload that Home Assistant cannot reject.
        temp_payload = {
            "name": "Room Temperature",
            "state_topic": TOPIC_TEMP_STATE,                     
            "unique_id": "esp32c3_v99_temp_entity",
            "device": device_definition
        }

        print("Publishing Switch Config...")
        client.publish(TOPIC_SWITCH_CONFIG, json.dumps(switch_payload), retain=True)
        time.sleep(0.5) 
        
        print("Publishing Temperature Config...")
        client.publish(TOPIC_TEMP_CONFIG, json.dumps(temp_payload), retain=True)
        time.sleep(0.5)
        
        print("Publishing Initial States...")
        client.publish(TOPIC_SWITCH_STATE, "OFF", retain=True)
        time.sleep(0.2)
        client.publish(TOPIC_TEMP_STATE, "26.0", retain=True)
        
        print("Initial baseline synchronization complete.")
        return True
    except Exception as e:
        print("!!! MQTT Setup Crash Error !!!:", e)
        return False

connect_mqtt()
print("All systems active! Main operation loop started.")

last_sensor_update = time.time() - 10
sensor_interval = 10

try:
    while True:
        try:
            client.check_msg()
            current_time = time.time()
            
            if current_time - last_sensor_update >= sensor_interval:
                print("Scanning for temperature sensors...")
                roms = ds.scan() 
                
                if roms:
                    print(f"Found {len(roms)} sensor(s). Reading temperature...")
                    ds.convert_temp()
                    time.sleep_ms(750)
                    for rom in roms:
                        temp = ds.read_temp(rom)
                        print(f"Telemetry Update -> Temperature: {temp:.2f}")
                        client.publish(TOPIC_TEMP_STATE, f"{temp:.2f}", retain=True)
                else:
                    print("Hardware Alert: No DS18B20 sensor answered on Pin 10.")
                
                last_sensor_update = current_time
                
            if int(time.time()) % 20 == 0:
                client.ping()
                time.sleep(1) 
                
        except (OSError, Exception) as err:
            print(f"\n[LOOP ERROR] Socket/Runtime issue: {err}")
            time.sleep(5)
            connect_mqtt()
        time.sleep(0.05)
except KeyboardInterrupt:
    print("Stopped.")
    client.disconnect()

