from machine import Pin
import time

# GPIO8 is the onboard blue LED on most ESP32-C3 Pro/Super Mini boards
# Note: These onboard LEDs are often inverted (0 = ON, 1 = OFF)
led = Pin(8, Pin.OUT)

print("Starting Blinking Loop... Press Ctrl+C in Shell to stop.")

while True:
    led.value(0)  # Turn LED ON
    time.sleep(0.5)
    led.value(1)  # Turn LED OFF
    time.sleep(0.5)
	
