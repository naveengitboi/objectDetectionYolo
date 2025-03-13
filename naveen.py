import serial
import time

# Initialize the serial connection
arduino = serial.Serial("COM5", 115200)
time.sleep(3)  # Give the Arduino time to initialize

dummy = "251"

try:
    while True:
        # Send data to Arduino
        arduino.write(dummy.encode('utf-8'))
        print(f"Sent to Arduino: {dummy}")

        # Wait for the Arduino to process the data and send a response
        time.sleep(0.1)

        # Read the response from Arduino
        if arduino.in_waiting > 0:  # Check if there is data available to read
            val = arduino.readline().decode('utf-8').strip()  # Read a complete line
            print(f"Value from Arduino: {val}")

        # Optional: Add a delay before the next iteration
        time.sleep(1)

except KeyboardInterrupt:
    print("Program terminated by user")

finally:
    # Close the serial connection
    arduino.close()
    print("Serial connection closed")