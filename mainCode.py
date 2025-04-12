from ultralytics import YOLO
from ultralytics.solutions import object_counter
import cv2
import math
from sort import *
import cvzone
import numpy as np
from time import time
from speedController import SpeedController
from arduinoFile import MotorController

# Configuration
PORT = "COM5"
BRATE = 9600
CONVEYOR_COORDS = [140, 0, 850, 1200]  # cx1, cy1, cx2, cy2
LINE_COORDS = [450, 152, 600, 152]  # lx, ly, rx, ry
CLASS_NAMES = ['typeOne', 'typeTwo', 'typeThree', 'typeFour']
SPEED_FACTOR = 1


def main():
    # Initialize components
    print("Initializing camera...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)

    print("Initializing model...")
    model = YOLO("runs/detect/train3/weights/best.pt")

    print("Initializing motor controller...")
    motor_controller = MotorController(PORT, BRATE)
    speed_controller = SpeedController()

    print("Initializing tracker...")
    tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
    total_obj_counts = []

    def lies_inside_box(x1, y1, x2, y2, box_coords):
        """Check if object is inside conveyor area"""
        cx1, cy1, cx2, cy2 = box_coords
        return x1 >= cx1 and x2 <= cx2 and y1 >= cy1 and y2 <= cy2

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera disconnected")
            break

        frame = cv2.flip(frame, 1)
        results = model.predict(source=frame, stream=True, conf=0.035)

        total_area = 0
        detections = np.empty((0, 5))
        cx1, cy1, cx2, cy2 = CONVEYOR_COORDS

        # Draw conveyor area
        cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (255, 0, 0), 3)

        # Process detections
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                if lies_inside_box(x1, y1, x2, y2, CONVEYOR_COORDS):
                    width, height = x2 - x1, y2 - y1
                    area = math.floor((width * height) / 1820)
                    total_area += area

                    # Draw detection
                    cvzone.cornerRect(frame, (x1, y1, width, height), cv2.LINE_AA)
                    confidence = math.ceil(box.conf[0].item() * 100) / 100
                    cls = int(box.cls[0].item())

                    cvzone.putTextRect(frame,
                                       f'{CLASS_NAMES[cls]} {confidence}',
                                       (max(0, x1), max(35, y1)),
                                       scale=2, thickness=1, offset=5)
                    cvzone.putTextRect(frame,
                                       f'{area} cm2',
                                       (max(0, x2), max(35, y2)),
                                       scale=2, thickness=1, offset=5)

                    detections = np.vstack([detections, [x1, y1, x2, y2, confidence]])

        # Update tracker and count objects
        tracker_results = tracker.update(detections)
        cv2.line(frame,
                 (LINE_COORDS[0], LINE_COORDS[1]),
                 (LINE_COORDS[2], LINE_COORDS[3]),
                 (0, 0, 255), 2)

        for res in tracker_results:
            x1, y1, x2, y2, obj_id = map(int, res)
            if lies_inside_box(x1, y1, x2, y2, CONVEYOR_COORDS):
                if obj_id not in total_obj_counts:
                    total_obj_counts.append(obj_id)

        # Calculate and set speed
        counted_objects = len(total_obj_counts)
        speed_updated = speed_controller.update_speed(counted_objects, total_area)

        if speed_updated:
            motor_controller.set_speed(speed_controller.get_current_speed() * SPEED_FACTOR)

        # Display info
        cvzone.putTextRect(frame, f'Area: {total_area} cm2', (0, 50), scale=2, thickness=1, offset=5)
        cvzone.putTextRect(frame, f'Objects: {counted_objects}', (300, 50), scale=2, thickness=1, offset=5)
        cvzone.putTextRect(frame,
                           f'Speed: {speed_controller.get_current_speed()}',
                           (600, 50),
                           scale=2, thickness=1, offset=5)

        cv2.imshow("Conveyor Monitoring", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    motor_controller.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()