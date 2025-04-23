from ultralytics import YOLO
import cv2
import math
import time
from sort import *
import cvzone
import numpy as np
from motor_controller_old import DualMotorController
from speedControllerDummy import DualMotorSpeedController
from motor_one_code import CONFIG, draw_conveyor_boundaries, process_frame
import shared_data_old

data_store = shared_data.DataStore()

# Conveyor belt parameters (adjustable)
belt_length = 100  # cm (total length of the belt)
belt_width = 16  # cm
current_speed = 5  # cm/s (default speed)
min_speed = 100  # cm/s (minimum speed when no waste detected)
max_speed = 500  # cm/s (maximum speed when waste detected)
detection_zone_height = 20  # cm (area at start where we detect waste)
frame_rate = 30  # Camera frame rate in fps
threshold_area = 10

# Calculate time needed for waste to travel full belt length
def calculate_movement_time(speed):
    return belt_length / speed if speed > 0 else 0

# Arduino serial communication setup
CONFIG['motor']['baudrate'] = 9600


def initialization_of_motor_two(shared_controller, shared_speed_controller):
    print("🚀 Initializing components...")
    cap = None
    try:
        # Use DirectShow backend for Windows
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Try to set FPS (may not work on all cameras)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        if not cap.isOpened():
            raise RuntimeError("Cannot open camera")
    except Exception as e:
        print(f"❌ Camera initialization failed: {str(e)}")
        raise

    model = YOLO(CONFIG['model']['path'])
    return cap, model, shared_controller, shared_speed_controller


def get_detection_zone(frame):
    """Define the detection zone at the start of the belt"""
    coords = CONFIG['conveyor']['coords']
    # Detection zone is at the start (top) of the conveyor
    top = int(coords[1])
    bottom = int(top + (detection_zone_height / belt_length) * (coords[3] - coords[1]))
    left = int(coords[0])
    right = int(coords[2])
    bottom = int(coords[3])
    left = int(coords[0])
    right = int(coords[2])
    return (top, bottom, left, right)


def detect_waste_in_zone(frame, zone, model):
    """Detect waste in the specified zone"""
    top, bottom, left, right = zone
    detections, total_area = process_frame(frame, model)
    return detections, total_area


def send_to_dashboard_motor_two(speed, objects, area, motor_class):
    # data_store.add_data(speed, objects, 0, motor_class)
    pass

def show_metrics_two(frame, area, speed, active):
    """Display real-time metrics on video feed"""
    status = "ACTIVE" if active else "IDLE"
    cvzone.putTextRect(frame, f'Area: {area} cm²', (0, 50),
                       scale=2, thickness=1, offset=5)
    cvzone.putTextRect(frame, f'Speed: {speed} cm/s', (600, 50),
                       scale=2, thickness=1, offset=5)
    cvzone.putTextRect(frame, f'Status: {status}', (300, 50),
                       scale=2, thickness=1, offset=5)


def motor_two_main(shared_controller, shared_speed_controller):
    cap = None
    motor_controller = None

    # State variables
    belt_active = False
    movement_end_time = 0
    current_speed = min_speed

    try:
        cap, model, motor_controller, speed_controller = initialization_of_motor_two(
            shared_controller, shared_speed_controller)
        # cv2.namedWindow("Conveyor Monitoring", cv2.WINDOW_NORMAL)
        # cv2.resizeWindow("Conveyor Monitoring", 800, 600)
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Camera disconnected for motor 2")
                break

            draw_conveyor_boundaries(frame)
            detection_zone = get_detection_zone(frame)

            # Draw detection zone
            top, bottom, left, right = detection_zone
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)

            # Check if belt should be moving
            current_time = time.time()
            if belt_active and current_time >= movement_end_time:
                belt_active = False
                current_speed = min_speed  # Reduce to minimum speed when not active
                motor_controller.set_speeds(motor2_speed=current_speed * CONFIG['motor']['speed_factor'])
                print("Belt movement completed, switching to idle mode")

            # Only check for new waste if belt is not active
            if not belt_active:
                detections, total_area = detect_waste_in_zone(frame, detection_zone, model)

                if total_area > threshold_area:  # Threshold for detection
                    belt_active = True
                    current_speed = max_speed
                    movement_time = calculate_movement_time(current_speed)
                    movement_end_time = current_time + movement_time
                    motor_controller.set_speeds(motor2_speed=current_speed * CONFIG['motor']['speed_factor'])
                    print(f"Waste detected! Moving belt for {movement_time:.2f} seconds at {current_speed}")

            # Update dashboard
            send_to_dashboard_motor_two(current_speed, 1 if belt_active else 0, total_area, 'pickup_belt')
            show_metrics_two(frame, total_area, current_speed, belt_active)

            cv2.imshow('Conveyor Belt - Motor 2', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


    except Exception as e:
        print(f"❌ Error in main loop: {str(e)}")

    finally:
        if cap is not None:
            cap.release()
        if motor_controller is not None:
            motor_controller.close()
        cv2.destroyAllWindows()
        print("✅ All resources released properly")


if __name__ == "__main__":
    # When run standalone
    controller = DualMotorController(CONFIG['motor']['port'], CONFIG['motor']['baudrate'])
    speed_controller = DualMotorSpeedController()
    motor_two_main(controller, speed_controller)