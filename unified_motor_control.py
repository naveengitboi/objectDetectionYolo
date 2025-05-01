from ultralytics import YOLO
import cv2
import math
import time
from sort import *
import cvzone
import numpy as np
from motor_controller import ConveyorSystemController
from speedController import DualMotorSpeedController
import shared_data
from threading import Lock

# Global configuration
CONFIG = {

    'cameras': [
        {  # Motor 1 Camera
            'port': 1,
            'width': 900,
            'height': 720,
            'flip': False,
            'name': "Segregation Belt",
            'motor_class': 'seg_belt',
            'conveyor': {
                'coords': [200, 0, 850, 720],
                'line_coords': [450, 152, 600, 152]
            },
            "area_scale_factor": 1.5
        },
        {
            'port': 2,
            'width': 1200,
            'height': 720,
            'flip': False,
            'name': "Pickup Belt",
            'motor_class': 'pickup_belt',
            'conveyor': {
                'coords': [200, 0, 850, 720],
                'detection_zone_height': 20  # cm
            },
            'belt_length': 100,  # cm
            'min_speed': 80,
            'max_speed': 250,
            'threshold_area': 5,
            "area_scale_factor": 0.9
        }
    ],


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
        'conveyor_color': (255, 0, 0),
        'conveyor_thickness': 3,
        'line_color': (0, 0, 255),
        'line_thickness': 2,
        'detection_zone_color': (0, 255, 255)
    }
}

# Global instances
data_store = shared_data.DataStore()
frame_lock = Lock()


class UnifiedMotorSystem:
    def __init__(self):
        self.controller = ConveyorSystemController('COM5', 9600)
        self.speed_controller = DualMotorSpeedController()
        self.caps = []
        self.models = []
        self.trackers = []
        self.tracked_objects = []
        self.camera_windows = []

        # Motor 2 specific states
        self.belt_active = False
        self.movement_end_time = 0
        self.is_motor2_speed_changed = 200

        # Add these for load cell handling
        self.last_valid_load = None
        self.load_stable_count = 0
        self.load_stable_threshold = 6  # Number of consistent readings needed
        self.last_load_send_time = 0
        self.load_send_interval = 10  # Minimum seconds between sends

    def initialize_cameras(self):
        print("🚀 Initializing cameras...")
        for i, cam_cfg in enumerate(CONFIG['cameras']):
            cap = None
            try:
                port = cam_cfg['port']
                if port == 1:
                    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(port, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg['width'])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg['height'])
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

                if not cap.isOpened():
                    raise RuntimeError(f"Camera {i} failed to open")

                self.caps.append(cap)
                self.models.append(YOLO(CONFIG['model']['path']))
                self.trackers.append(Sort(max_age=20, min_hits=3, iou_threshold=0.3))
                self.tracked_objects.append([])
                self.camera_windows.append(cam_cfg['name'])

                print(f"✅ Camera {i} ({cam_cfg['name']}) initialized successfully")

            except Exception as e:
                print(f"❌ Camera {i} initialization failed: {str(e)}")
                if cap:
                    cap.release()
                raise

    def process_motor1_frame(self, frame_idx, frame):
        cam_cfg = CONFIG['cameras'][frame_idx]

        self.draw_conveyor_boundaries(frame, cam_cfg)
        area_factor = cam_cfg['area_scale_factor']

        detections, total_area = self.process_frame(frame, frame_idx)
        total_area = total_area*area_factor
        tracker_results = self.trackers[frame_idx].update(detections)

        for res in tracker_results:
            x1, y1, x2, y2, obj_id = map(int, res)
            if self.is_inside_conveyor(x1, y1, x2, y2, frame_idx) and obj_id not in self.tracked_objects[frame_idx]:
                self.tracked_objects[frame_idx].append(obj_id)

        counted_objects = len(self.tracked_objects[frame_idx])
        speed_updated = self.speed_controller.update_motor1_speed(counted_objects, total_area)
        current_speed = self.speed_controller.get_motor1_speed()
        current_motor2_speed = self.controller.motor_speeds['motor2']

        if speed_updated:
            self.controller.set_motor_speeds(current_speed, current_motor2_speed)
            self.send_to_dashboard(current_speed, counted_objects, total_area, cam_cfg['motor_class'])

        # Show metrics
        self.show_metrics(frame, total_area, current_speed, counted_objects, cam_cfg['name'])

        return frame

    def process_motor2_frame(self, frame_idx, frame):
        cam_cfg = CONFIG['cameras'][frame_idx]
        area_factor = cam_cfg['area_scale_factor']
        self.draw_conveyor_boundaries(frame, cam_cfg)
        detection_zone = self.get_detection_zone(frame, frame_idx)
        top, bottom, left, right = detection_zone
        cv2.rectangle(frame, (left, top), (right, bottom), CONFIG['visualization']['detection_zone_color'], 2)
        current_time = time.time()
        current_speed = cam_cfg['min_speed']
        total_area = 0
        if self.belt_active and current_time >= self.movement_end_time:
            self.belt_active = False
            current_speed = cam_cfg['min_speed']
            current_motor1_speed = self.controller.motor_speeds['motor1']
            self.controller.set_motor_speeds(current_motor1_speed, current_speed * CONFIG['motor']['speed_factor'])
            print("Belt movement completed, switching to idle mode")

        # Detect waste if belt is idle
        if not self.belt_active:
            detections, total_area = self.process_frame(frame, frame_idx)
            total_area = total_area * area_factor
            if total_area > cam_cfg['threshold_area']:
                self.belt_active = True
                current_speed = cam_cfg['max_speed']
                # movement_time = cam_cfg['belt_length'] / current_speed
                movement_time = 3
                self.movement_end_time = current_time + movement_time
                current_motor1_speed = self.controller.motor_speeds['motor1']
                self.controller.set_motor_speeds(current_motor1_speed, current_speed * CONFIG['motor']['speed_factor'])
                print(f"Waste detected! Moving belt for {movement_time:.2f} seconds at {current_speed}")

        if self.is_motor2_speed_changed != current_speed:
            self.send_to_dashboard(current_speed, 0, total_area, cam_cfg['name'])
            self.is_motor2_speed_changed = current_speed
        # Show metrics
        self.show_metrics(frame, total_area, current_speed, self.belt_active, cam_cfg['name'])

        return frame

    def check_load_cell_value(self):
        current_load = self.controller.get_load_cell_value()
        current_time = time.time()
        if (current_time - self.last_load_send_time) < self.load_send_interval:
            return
        if current_load < 0 or current_load > 2000:  # Example range
            print(f"Invalid load reading: {current_load}")
            return
        if self.last_valid_load is not None:
            if abs(current_load - self.last_valid_load) < 2.0:  # Within 2 units
                self.load_stable_count += 1
            else:
                self.load_stable_count = 0
        self.last_valid_load = current_load
        if self.load_stable_count >= self.load_stable_threshold:
            self.send_load_to_dashboard(current_load)
            self.last_load_send_time = current_time
            self.load_stable_count = 0

    def draw_conveyor_boundaries(self, frame, cam_cfg):
        coords = cam_cfg['conveyor']['coords']
        cv2.rectangle(
            frame,
            (coords[0], coords[1]),
            (coords[2], coords[3]),
            CONFIG['visualization']['conveyor_color'],
            CONFIG['visualization']['conveyor_thickness']
        )

    def get_detection_zone(self, frame, frame_idx):
        cam_cfg = CONFIG['cameras'][frame_idx]
        coords = cam_cfg['conveyor']['coords']
        top = int(coords[1])
        bottom = int(
            top + (cam_cfg['conveyor']['detection_zone_height'] / cam_cfg['belt_length']) * (coords[3] - coords[1]))
        left = int(coords[0])
        right = int(coords[2])

        bottom = int(coords[3])
        left = int(coords[0])
        right = int(coords[2])
        return (top, bottom, left, right)

    def is_inside_conveyor(self, x1, y1, x2, y2, frame_idx):
        coords = CONFIG['cameras'][frame_idx]['conveyor']['coords']
        return x1 >= coords[0] and x2 <= coords[2] and y1 >= coords[1] and y2 <= coords[3]

    def process_frame(self, frame, frame_idx):
        total_area = 0
        detections = np.empty((0, 5))

        results = self.models[frame_idx].predict(
            source=frame,
            stream=True,
            conf=CONFIG['model']['conf_threshold']
        )

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                if self.is_inside_conveyor(x1, y1, x2, y2, frame_idx):
                    width, height = x2 - x1, y2 - y1
                    area = math.floor((width * height) / 1820)
                    total_area += area

                    # Draw detection
                    self.draw_detection(frame, x1, y1, width, height,
                                      box.conf[0].item(), int(box.cls[0].item()),
                                      area, frame_idx)

                    detections = np.vstack([detections, [x1, y1, x2, y2, box.conf[0].item()]])

        return detections, total_area

    def draw_detection(self, frame, x1, y1, width, height, confidence, cls_id, area, frame_idx):
        cvzone.cornerRect(frame, (x1, y1, width, height), cv2.LINE_AA)
        cvzone.putTextRect(
            frame,
            f'{CONFIG["classes"][cls_id]} {confidence:.2f}',
            (max(0, x1), max(35, y1)),
            scale=2, thickness=1, offset=5
        )
        cvzone.putTextRect(
            frame,
            f'{area} cm²',
            (max(0, x1 + width), max(35, y1)),
            scale=2, thickness=1, offset=5
        )

    def show_metrics(self, frame, area, speed, active_or_objects, name):

        area = math.floor(area)
        if "pickup" in name.lower():
            status = "ACTIVE" if active_or_objects else "IDLE"
            cvzone.putTextRect(frame, f'Status: {status}', (300, 50),
                              scale=2, thickness=1, offset=5)
        else:
            cvzone.putTextRect(frame, f'Objects: {active_or_objects}', (300, 50),
                              scale=2, thickness=1, offset=5)

        cvzone.putTextRect(frame, f'Area: {area} cm²', (0, 50),
                          scale=2, thickness=1, offset=5)
        cvzone.putTextRect(frame, f'Speed: {speed}', (600, 50),
                          scale=2, thickness=1, offset=5)

    def send_to_dashboard(self, speed, objects, area, motor_class):
        data_store.add_data(speed, objects, area, motor_class)

    def send_load_to_dashboard(self, load_value):
        if load_value <= 0:
            return
        load_value = math.floor(load_value)
        data_store.add_load_data( "type_one",load_value)
        print(f"Sent load to dashboard: {load_value:.2f}")


    def run(self):
        try:
            self.initialize_cameras()

            for window in self.camera_windows:
                cv2.namedWindow(window, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window, 800, 600)

            while True:
                frames = []
                for i, cap in enumerate(self.caps):
                    ret, frame = cap.read()
                    if not ret:
                        print(f"❌ Camera {i} disconnected")
                        continue

                    if CONFIG['cameras'][i]['flip']:
                        frame = cv2.flip(frame, 1)

                    if "pickup" in CONFIG['cameras'][i]['name'].lower():
                        frame = self.process_motor2_frame(i, frame)
                    else:
                        frame = self.process_motor1_frame(i, frame)

                    frames.append((i, frame))

                for i, frame in frames:
                    cv2.imshow(self.camera_windows[i], frame)
                self.check_load_cell_value()
                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"❌ Error in main loop: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        print("🧹 Cleaning up resources...")
        for cap in self.caps:
            if cap is not None and cap.isOpened():
                cap.release()

        self.controller.set_motor_speeds(0, 0)
        self.controller.close()
        cv2.destroyAllWindows()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    system = UnifiedMotorSystem()
    system.run()