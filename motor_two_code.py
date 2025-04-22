from ultralytics import YOLO
import cv2
import math
from sort import *
import cvzone
import numpy as np
from motor_controller import DualMotorController
from speedControllerDummy import DualMotorSpeedController
from motor_one_code import CONFIG, draw_conveyor_boundaries, process_frame
import shared_data


data_store = shared_data.DataStore()

# Conveyor belt parameters (adjustable)
belt_width = 16  # cm
step_height = 8  # cm
num_steps = 4  # Total steps on the belt
belt_speed = 5  # cm/s (adjust dynamically if needed)
frame_rate = 30  # Camera frame rate in fps
frame_skips = 3

# ROI dimensions based on belt parameters
roi_height = int((CONFIG['conveyor']['coords'][3]-CONFIG['conveyor']['coords'][1])/num_steps)
roi_width =CONFIG['conveyor']['coords'][2]-CONFIG['conveyor']['coords'][0]

# Arduino serial communication setup

CONFIG['motor']['baudrate'] = 9600

def initialization_of_motor_two(shared_controller, shared_speed_controller):
    print("🚀 Initializing components for Motor 2...")
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG['camera']['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG['camera']['height'])

    model = YOLO(CONFIG['model']['path'])
    return cap, model, shared_controller, shared_speed_controller

# Function to calculate ROIs dynamically
def calculate_rois(frame_height, frame_width):
    rois = []
    coords = CONFIG['conveyor']['coords']
    for step in range(num_steps):
        top = int(coords[1] + step*roi_height)
        bottom = int(coords[3] + step * roi_height)
        left = int(coords[0])
        right = int(left + roi_width)
        rois.append((top, bottom, left, right))
    return rois

# Function to detect waste in an ROI
def detect_waste(frame, roi, model):
    top, bottom, left, right = roi
    roi_frame = frame[top:bottom, left:right]
    # gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
    # _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    # contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections, total_area = process_frame(roi_frame, model)
    return detections, total_area

def send_to_dashboard_motor_two(speed, objects, area, motor_class):
    data_store.add_data(speed, objects, 0, motor_class)

def draw_rois(rois, frame):
    # function not used
    for idx, roi in enumerate(rois):
        top, bottom, left, right = roi
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

def show_metrics_two(frame, area, speed):
    """Display real-time metrics on video feed"""
    cvzone.putTextRect(frame, f'Area: {area} cm²', (0, 50),
                       scale=2, thickness=1, offset=5)
    cvzone.putTextRect(frame, f'Speed: {speed}', (600, 50),
                       scale=2, thickness=1, offset=5)


def motor_two_main(shared_controller, shared_speed_controller):
    cap, model, motor_controller, speed_controller = initialization_of_motor_two(shared_controller,
                                                                                 shared_speed_controller)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rois = calculate_rois(frame_height, frame_width)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Camera disconnected for motor 2")
                break

            draw_conveyor_boundaries(frame)
            step_status = []
            area_till_now = 0

            for roi in rois:
                detections, total_area = detect_waste(frame, roi, model)
                area_till_now += total_area
                step_status.append(1 if total_area > 5 else 0)

            should_update_speed = speed_controller.update_motor2_speed(step_status)
            current_speed = speed_controller.get_motor2_speed()

            if should_update_speed:
                motor_controller.set_speeds(motor2_speed=current_speed * CONFIG['motor']['speed_factor'])
                send_to_dashboard_motor_two(current_speed, len(step_status), area_till_now, 'pickup_belt')

            show_metrics_two(frame, area_till_now, current_speed)

            for idx, roi in enumerate(rois):
                top, bottom, left, right = roi
                color = (0, 255, 0) if step_status[idx] else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            cv2.imshow('Conveyor Belt - Motor 2', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Motor 2 process interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Motor 2 resources released.")


if __name__ == "__main__":
    # When run standalone
    controller = DualMotorController(CONFIG['motor']['port'], CONFIG['motor']['baudrate'])
    speed_controller = DualMotorSpeedController()
    motor_two_main(controller, speed_controller)