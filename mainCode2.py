from ultralytics import YOLO
import cv2
import math
from sort import *
import cvzone
import numpy as np
from datetime import datetime
from speedController import SpeedController
from arduinoFile import MotorController
import shared_data


data_store = shared_data.DataStore()

# Configuration
CONFIG = {
    'camera': {
        'port': 0,
        'width': 1920,
        'height': 1200,
        'flip': True
    },
    'conveyor': {
        'coords': [140, 0, 850, 1200],  # cx1, cy1, cx2, cy2
        'line_coords': [450, 152, 600, 152]  # lx, ly, rx, ry
    },
    'model': {
        'path': "runs/detect/train3/weights/best.pt",
        'conf_threshold': 0.035
    },
    'motor': {
        'port': "COM5",
        'baudrate': 9600,
        'speed_factor': 1
    },
    'classes': ['typeOne', 'typeTwo', 'typeThree', 'typeFour'],
    'visualization': {
        'conveyor_color': (255, 0, 0),  # Blue in BGR
        'conveyor_thickness': 3,
        'line_color': (0, 0, 255),  # Red in BGR
        'line_thickness': 2
    }
}


def initialize_components():
    """Initialize all hardware and models"""
    print("🚀 Initializing components...")

    # Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG['camera']['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG['camera']['height'])

    # Models
    model = YOLO(CONFIG['model']['path'])
    tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)

    # Hardware
    motor_controller = MotorController(
        CONFIG['motor']['port'],
        CONFIG['motor']['baudrate']
    )
    speed_controller = SpeedController()

    return cap, model, tracker, motor_controller, speed_controller


def draw_conveyor_boundaries(frame):
    """Draw conveyor bounding box and counting line"""
    # Draw conveyor bounding box
    cv2.rectangle(
        frame,
        (CONFIG['conveyor']['coords'][0], CONFIG['conveyor']['coords'][1]),
        (CONFIG['conveyor']['coords'][2], CONFIG['conveyor']['coords'][3]),
        CONFIG['visualization']['conveyor_color'],
        CONFIG['visualization']['conveyor_thickness']
    )

    # Draw counting line
    cv2.line(
        frame,
        (CONFIG['conveyor']['line_coords'][0], CONFIG['conveyor']['line_coords'][1]),
        (CONFIG['conveyor']['line_coords'][2], CONFIG['conveyor']['line_coords'][3]),
        CONFIG['visualization']['line_color'],
        CONFIG['visualization']['line_thickness']
    )


def is_inside_conveyor(x1, y1, x2, y2):
    """Check if detection is within conveyor bounds"""
    cx1, cy1, cx2, cy2 = CONFIG['conveyor']['coords']
    return x1 >= cx1 and x2 <= cx2 and y1 >= cy1 and y2 <= cy2


def draw_detection(frame, x1, y1, width, height, confidence, cls_id, area):
    """Visualize detections on frame"""
    cvzone.cornerRect(frame, (x1, y1, width, height), cv2.LINE_AA)
    cvzone.putTextRect(frame,
                       f'{CONFIG["classes"][cls_id]} {confidence:.2f}',
                       (max(0, x1), max(35, y1)),
                       scale=2, thickness=1, offset=5)
    cvzone.putTextRect(frame,
                       f'{area} cm²',
                       (max(0, x1 + width), max(35, y1)),
                       scale=2, thickness=1, offset=5)


def process_frame(frame, model):
    """Run object detection and return metrics"""
    total_area = 0
    detections = np.empty((0, 5))

    results = model.predict(source=frame, stream=True,
                            conf=CONFIG['model']['conf_threshold'])

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if is_inside_conveyor(x1, y1, x2, y2):
                width, height = x2 - x1, y2 - y1
                area = math.floor((width * height) / 1820)
                total_area += area

                # Draw detection
                draw_detection(frame, x1, y1, width, height,
                               box.conf[0].item(), int(box.cls[0].item()),
                               area)

                detections = np.vstack([detections, [x1, y1, x2, y2, box.conf[0].item()]])

    return detections, total_area


def update_object_counts(tracker_results, tracked_objects):
    """Maintain list of unique object IDs crossing the line"""
    for res in tracker_results:
        x1, y1, x2, y2, obj_id = map(int, res)
        if is_inside_conveyor(x1, y1, x2, y2) and obj_id not in tracked_objects:
            tracked_objects.append(obj_id)


def send_to_dashboard(speed, objects, area):
    data_store.add_data(speed, objects, area)

def show_metrics(frame, area, objects, speed):
    """Display real-time metrics on video feed"""
    cvzone.putTextRect(frame, f'Area: {area} cm²', (0, 50),
                       scale=2, thickness=1, offset=5)
    cvzone.putTextRect(frame, f'Objects: {objects}', (300, 50),
                       scale=2, thickness=1, offset=5)
    cvzone.putTextRect(frame, f'Speed: {speed}', (600, 50),
                       scale=2, thickness=1, offset=5)


def main():
    cap, model, tracker, motor_controller, speed_controller = initialize_components()
    tracked_objects = []

    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                print("❌ Camera disconnected")
                break

            if CONFIG['camera']['flip']:
                frame = cv2.flip(frame, 1)

            # Draw conveyor boundaries FIRST (background)
            draw_conveyor_boundaries(frame)

            # Process detections
            detections, total_area = process_frame(frame, model)

            # Update tracker
            tracker_results = tracker.update(detections)
            update_object_counts(tracker_results, tracked_objects)

            # Calculate metrics
            counted_objects = len(tracked_objects)
            speed_updated = speed_controller.update_speed(counted_objects, total_area)
            current_speed = speed_controller.get_current_speed()

            # Send to dashboard
            send_to_dashboard(current_speed, counted_objects, total_area)

            # Control motor only if speed changed significantly
            if speed_updated:
                motor_controller.set_speed(current_speed * CONFIG['motor']['speed_factor'])

            # Display UI metrics (on top of everything)
            show_metrics(frame, total_area, counted_objects, current_speed)

            # Show final frame
            cv2.imshow("Conveyor Monitoring", frame)

            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        motor_controller.close()
        print("✅ Resources cleaned up")


if __name__ == "__main__":
    main()