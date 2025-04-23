import serial
import time
from threading import Thread, Lock
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ConveyorSystemController:
    def __init__(self, port, baudrate=9600):
        self.serial_port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.lock = Lock()
        self.running = False
        self.load_cell_value = 0.0
        self.motor_speeds = {'motor1': 0, 'motor2': 0}
        self.arduino_ready = False

        logging.info(f"Initializing ConveyorSystemController for port {port}")

        try:
            # Initialize serial connection with retries
            self._initialize_serial_with_retry(max_retries=3, retry_delay=2)

            # Start serial reader thread
            self.reader_thread = Thread(target=self._read_serial_data)
            self.reader_thread.daemon = True
            self.running = True
            self.reader_thread.start()

            # Wait for Arduino to initialize
            if not self._wait_for_arduino(timeout=15):
                raise RuntimeError("Arduino failed to become ready")

            logging.info("Controller initialization complete")

        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            self.close()
            raise

    def _initialize_serial_with_retry(self, max_retries=3, retry_delay=2):
        """Initialize serial connection with retry logic"""
        for attempt in range(max_retries):
            try:
                logging.debug(f"Attempt {attempt + 1} to open serial port")
                self.serial_conn = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.baudrate,
                    timeout=5,
                    write_timeout=5
                )

                # Wait for connection to stabilize
                time.sleep(2)

                # Clear buffers
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()

                logging.info(f"✅ Serial connection established on {self.serial_port}")
                return

            except serial.SerialException as e:
                logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
            except Exception as e:
                logging.error(f"Unexpected error during serial init: {str(e)}")
                raise

    def _wait_for_arduino(self, timeout=10):
        """Wait for Arduino ready signal with timeout"""
        start_time = time.time()
        logging.debug("Waiting for Arduino READY signal...")

        while time.time() - start_time < timeout:
            # Check if reader thread already saw the READY signal
            if self.arduino_ready:
                logging.info("Arduino system ready (via reader thread)")
                return True

            # Direct check of serial port
            if self.serial_conn and self.serial_conn.in_waiting:
                try:
                    line = self.serial_conn.readline().decode().strip()
                    logging.debug(f"Direct read received: {line}")

                    if line == "READY":
                        self.arduino_ready = True
                        logging.info("Arduino system ready (direct read)")
                        return True

                except Exception as e:
                    logging.warning(f"Error reading during ready check: {str(e)}")

            time.sleep(0.1)

        # Final check in case reader thread got it
        if self.arduino_ready:
            logging.info("Arduino system ready (final check)")
            return True

        logging.error("Timeout waiting for Arduino READY signal")
        return False

    def _read_serial_data(self):
        """Thread for reading serial data"""
        logging.debug("Serial reader thread started")
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode().strip()
                    logging.debug(f"Serial received: {line}")

                    with self.lock:
                        if line == "READY":
                            self.arduino_ready = True
                            logging.info("Arduino ready detected in reader thread")

                        elif line.startswith("LOAD:"):
                            try:
                                self.load_cell_value = float(line[5:])
                                logging.debug(f"Updated load cell: {self.load_cell_value}")
                            except ValueError:
                                logging.warning(f"Invalid load value: {line}")

                        elif line.startswith("ACK:"):
                            try:
                                speeds = line[4:].split(',')
                                self.motor_speeds['motor1'] = int(speeds[0])
                                self.motor_speeds['motor2'] = int(speeds[1])
                                logging.debug(f"Updated motor speeds: {self.motor_speeds}")
                            except (IndexError, ValueError):
                                logging.warning(f"Invalid motor ACK: {line}")

                        elif line.startswith("ERR:"):
                            logging.error(f"Arduino error: {line[4:]}")

                        elif line == "ACK:TARE_STARTED":
                            logging.info("Tare started")

                        elif line.startswith("ACK:CALIBRATION:"):
                            logging.info(f"Calibration: {line[15:]}")

            except serial.SerialException as e:
                logging.error(f"Serial error in reader thread: {str(e)}")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Unexpected error in reader thread: {str(e)}")
                time.sleep(1)

    def set_motor_speeds(self, motor1_speed, motor2_speed):
        """
        Set speeds for both motors
        Format: "speed1,speed2"
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logging.error("Serial connection not available")
            return False

        # Constrain speeds to valid range
        motor1_speed = max(-1000, min(1000, motor1_speed))
        motor2_speed = max(-1000, min(1000, motor2_speed))

        command = f"{motor1_speed},{motor2_speed}\n"

        try:
            with self.lock:
                self.serial_conn.write(command.encode('utf-8'))
                logging.debug(f"Sent motor command: {command.strip()}")
                return True
        except Exception as e:
            logging.error(f"Failed to send motor command: {str(e)}")
            return False

    def get_load_cell_value(self):
        """Get the latest load cell reading"""
        with self.lock:
            return self.load_cell_value

    def tare_load_cell(self):
        """Send tare command to load cell"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return False

        try:
            with self.lock:
                self.serial_conn.write(b"t\n")
                return True
        except Exception as e:
            logging.error(f"Failed to send tare command: {str(e)}")
            return False

    def calibrate_load_cell(self, known_mass):
        """
        Initiate load cell calibration with known mass
        """
        if known_mass <= 0:
            logging.error("Known mass must be positive")
            return False

        try:
            with self.lock:
                # Start calibration process
                self.serial_conn.write(b"r\n")
                # Wait for Arduino to be ready for mass input
                time.sleep(1)
                # Send the known mass value
                self.serial_conn.write(f"{known_mass:.2f}\n".encode('utf-8'))
                logging.info(f"Sent calibration mass: {known_mass:.2f}")
                return True
        except Exception as e:
            logging.error(f"Failed to send calibration command: {str(e)}")
            return False

    def stop_motors(self):
        """Stop both motors (set speeds to 0)"""
        return self.set_motor_speeds(0, 0)

    def close(self):
        """Clean up resources"""
        self.running = False
        if self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        if self.serial_conn and self.serial_conn.is_open:
            self.stop_motors()
            time.sleep(0.1)
            self.serial_conn.close()
            logging.info("Serial connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Destructor"""
        self.close()