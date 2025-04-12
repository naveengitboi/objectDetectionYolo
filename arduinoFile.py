import serial
import time

class MotorController:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.last_speed_change = 0
        self.current_speed = 0
        time.sleep(2)  # Wait for Arduino to initialize

    def set_speed(self, speed):
        """Send speed command to Arduino"""
        self.ser.write(f"{speed}\n".encode('utf-8'))
        self.current_speed = speed
        time.sleep(0.1)
        return True

    def close(self):
        """Clean up serial connection"""
        self.ser.close()