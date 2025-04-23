import serial
import time

ser = serial.Serial('COM5', 9600, timeout=5)  # Replace 'COM5' with your port
start_time = time.time()

while time.time() - start_time < 10:  # Wait up to 10 seconds
    if ser.in_waiting:
        line = ser.readline().decode().strip()
        print("Received:", line)
        if line == "READY":
            print("✅ Arduino is ready!")
            break
else:
    print("❌ Timeout: No response from Arduino")