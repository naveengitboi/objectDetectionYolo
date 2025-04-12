import serial
import time


class StepperMotorController:
    def __init__(self, port, baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino to initialize
        self._read_serial()  # Clear any initial messages

    def _read_serial(self):
        while self.ser.in_waiting > 0:
            print(self.ser.readline().decode('utf-8').strip())

    def set_speed(self, speed):
        """Set motor speed in steps per second"""
        self.ser.write(f"{speed}\n".encode('utf-8'))
        time.sleep(0.1)
        self._read_serial()

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    # Example usage
    PORT = 'COM5'  # Change this to your Arduino's port (e.g., '/dev/ttyUSB0' on Linux)
    controller = StepperMotorController(PORT)
    try:
        print("Stepper Motor Control")
        print("Enter speed values (positive/negative integers). Type 'quit' to exit.")

        while True:
            user_input = input("Enter speed (steps/sec): ")

            if user_input.lower() == 'quit':
                break

            try:
                speed = int(user_input)
                controller.set_speed(speed)
            except ValueError:
                print("Please enter a valid integer or 'quit'")

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        controller.close()
        print("Connection closed")