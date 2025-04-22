import serial
import time
from threading import Lock

class DualMotorController:
    def __init__(self, port, baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.lock = Lock()  # Thread-safe serial communication
        self.current_speeds = {'motor1': 0, 'motor2': 0}
        time.sleep(2)  # Wait for Arduino initialization

    def set_speeds(self, motor1_speed=None, motor2_speed=None):
        """Thread-safe method to update motor speeds"""
        with self.lock:
            # Update only the specified motors
            if motor1_speed is not None:
                self.current_speeds['motor1'] = motor1_speed
            if motor2_speed is not None:
                self.current_speeds['motor2'] = motor2_speed

            # Send combined command
            command = f"{self.current_speeds['motor1']},{self.current_speeds['motor2']}\n"
            self.ser.write(command.encode('utf-8'))
            time.sleep(0.01)  # Small delay to prevent serial overflow

    def close(self):
        """Clean up serial connection"""
        with self.lock:
            self.ser.close()