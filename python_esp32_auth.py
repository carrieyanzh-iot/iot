import sys
import ssl
import time
import network
import ntptime
import gc
from umqtt.simple import MQTTClient

# Force modern SSL mapping to handle older third-party umqtt library dependencies
sys.modules['ussl'] = ssl 

# =========================================================================
# 1. DEFINE CONFIGURATION VARIABLES
# =========================================================================
CLIENT_ID = "esp32c3_master_final_v99"
MQTT_PASS = ""
DEVICE_NAME = "ESP32-C3 Final Suite"
BROKER_IP = "192.168.1.122"  # Your Raspberry Pi Home Assistant IP

WIFI_SSID = "ASUS-MyHome"
WIFI_PASS = "passowrd"

# =========================================================================
# 2. WI-FI & TIME INTERFACE FUNCTIONS
# =========================================================================
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Connecting to Wi-Fi network: {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        
        # Timeout safety tracker (stop waiting after 15 seconds)
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")
            
    if wlan.isconnected():
        print("\nWi-Fi Connected successfully!")
        print("Device Network Configuration Info:", wlan.ifconfig())
        return True
    else:
        print("\nWi-Fi Connection failed. Verify credentials.")
        return False

def sync_time_from_net():
    import machine
    
    # Standard public time servers
    ntp_servers = ["pool.ntp.org", "time.google.com", "time.windows.com", BROKER_IP]
    
    for server in ntp_servers:
        print(f"Attempting time sync via: {server}...")
        try:
            ntptime.host = server
            ntptime.settime()
            print("System time synchronized successfully!")
            print("Current Synced Time (UTC):", time.localtime())
            return True
        except Exception as e:
            print(f"Server {server} dropped request.")
            
    # --- HARDWARE OVERRIDE BACKUP ---
    print("Network time servers unreachable. Injecting manual 2026 timeline calibration override...")
    try:
        rtc = machine.RTC()
        rtc.datetime((2026, 9, 28, 1, 22, 30, 0, 0))
        print("Manual timeline calibration injected. Fake Current Time (UTC):", time.localtime())
        return True
    except Exception as e:
        print("Manual calibration failure:", e)
        return False

# =========================================================================
# 3. DEFINE THE MESSAGE CALLBACK FUNCTION
# =========================================================================
def mqtt_callback(topic, msg):
    command = msg.decode('utf-8')
    print(f"Home Assistant Command Received: {command}")


# ==========================================
# 4. READ SECURITY CERTIFICATES & SETUP SSL
# ==========================================
print("Loading cryptographic assets from flash...")
try:
    with open("esp32.key", "rb") as f:
        device_key = f.read()

    with open("esp32.crt", "rb") as f:
        device_cert = f.read()

    with open("ca.crt", "rb") as f:
        ca_cert = f.read()

    # Build the official SSL Context Object
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_cert_chain(device_cert, device_key)
    context.load_verify_locations(cadata=ca_cert)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    print("SSL Cryptographic Context generated successfully.")
except Exception as e:
    print("Critical Error loading certificates from flash:", e)
    sys.exit()



# ==========================================
# 5. INITIALIZE THE GLOBAL MQTT CLIENT VARIABLE
# ==========================================
client = MQTTClient(
    client_id=CLIENT_ID,
    server=BROKER_IP,
    port=8883,
    ssl=context  # Inject the formal SSL context object cleanly
)

# ==========================================
# 6. RUN THE SYSTEM APPLICATION INITIALIZER
# ==========================================
print("Booting ESP32-C3 System...")

if connect_to_wifi():
    if sync_time_from_net():
        print("Initializing secure MQTT setup...")
        try:
            gc.collect()
            client.set_callback(mqtt_callback)
            
            print("Connecting securely to Broker on port 8883...")
            client.connect()
            print("Connected securely using mTLS!")
            
            while True:
                client.check_msg()
                time.sleep(1)
                
        except Exception as e:
            print("Failed to initialize secure loop:", e)
    else:
        print("System halted: Cannot authenticate certificates without correct clock sync.")
else:
    print("System halted: Missing operational network interface link.")

