import serial
import time
from threading import Lock
import logging

class DualMotorController:
    def __init__(self, port, baudrate=9600):
        self.ser = None
        self.lock = Lock()
        self.current_speeds = {'motor1': 0, 'motor2': 0}
        self.port = port
        self.baudrate = baudrate
        self._initialize_serial()

    def _initialize_serial(self):
        """Initialize serial connection with proper error handling"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            if not self.ser.is_open:
                raise RuntimeError(f"Failed to open port {self.port}")
            time.sleep(2)  # Wait for Arduino to initialize
            print(f"✅ Serial port {self.port} initialized successfully")
        except Exception as e:
            print(f"❌ Serial port initialization failed: {str(e)}")
            self.ser = None

    def set_speeds(self, motor1_speed=None, motor2_speed=None):
        """Thread-safe method to update motor speeds"""
        if self.ser is None or not self.ser.is_open:
            print("⚠️ Serial port not available, cannot set speeds")
            return

        with self.lock:
            try:
                # Update only the specified motors
                if motor1_speed is not None:
                    self.current_speeds['motor1'] = motor1_speed
                if motor2_speed is not None:
                    self.current_speeds['motor2'] = motor2_speed

                # Send combined command
                command = f"{self.current_speeds['motor1']},{self.current_speeds['motor2']}\n"
                self.ser.write(command.encode('utf-8'))
                time.sleep(0.01)  # Small delay to prevent serial overflow
            except Exception as e:
                print(f"❌ Error setting speeds: {str(e)}")

    def close(self):
        """Clean up serial connection safely"""
        with self.lock:
            if self.ser is not None:
                try:
                    if self.ser.is_open:
                        # Send stop command before closing
                        self.ser.write("0,0\n".encode('utf-8'))
                        time.sleep(0.1)
                        self.ser.close()
                        print("✅ Serial port closed properly")
                except Exception as e:
                    print(f"❌ Error closing serial port: {str(e)}")
                finally:
                    self.ser = None

    def __del__(self):
        """Destructor to ensure proper cleanup"""
        self.close()