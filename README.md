# Speed Controlling Based on Area Detection using YOLOv8n Model

## Introduction
This project implements a proportional control system to regulate the speed of conveyor belt motors based on the observed load, measured as the area of objects detected by a YOLOv8n model. It incorporates various technologies and methodologies to ensure accurate object detection, data management, and real-time adjustments. 

---

## Initial Instructions
1. Clone this Git repository to your local machine.
2. Open the folder in your preferred Python IDE, such as VS Code, PyCharm, Eclipse, or VIM/NVIM.

---

## Concept Overview

### Core Principle
The speed of conveyor motors is controlled proportionally to the detected load on the conveyor belt. The relationship ensures heavier loads result in slower motor speeds, while lighter or no loads allow for higher speeds or halting. This behavior is implemented using the formula:

```
ActualSpeed = (k1 * Area + k2 * Counts) * ScaleFactor
```
Where:
- **k1** and **k2** are constants.

### Camera Placement Challenges
Accurate area detection depends on the camera's placement. Variations in height, angle, and position can lead to inconsistent results. To address this, a scaling factor was introduced to normalize measurements based on camera height, providing consistent area calculations.

---

## Coding Components

### Technologies Used

- **OpenCV-Python:** Captures and processes video frames from the camera.
- **Sort Tracker:** Tracks objects, assigns unique IDs, and facilitates object counting.
- **Ultralytics:** Provides YOLO-based object detection for real-time analysis.
- **PySerial:** Ensures seamless communication between Python and Arduino.
- **Dash Plotly:** Creates an interactive dashboard displaying metrics such as speed, area, and load.
- **SQLite3:** Manages a database for storing key metrics, supporting analysis and visualization.

### Key Functions and Modules

#### Main Python Script: `unified_motor_control.py`

1. **UnifiedMotorSystem Class:**
   - Manages the operation of two motors.
   - Simplifies tasks with helper functions for smooth execution.

2. **Configuration Setup:**
   - **CONFIG Dictionary:** Stores key parameters, including:
     - Conveyor dimensions.
     - Camera and motor settings.
     - YOLO model path and confidence threshold.
     - Waste classification.
   - **data_store:** Links to an SQLite3 database, creating a new file if none exists.

#### Helper Functions

- **`draw_conveyor_boundaries()`**: Draws boundary rectangles around the conveyor belt.
- **`is_inside_conveyor()`**: Checks if an object lies within conveyor boundaries.
- **`show_metrics()`**: Displays metrics (area, speed, object count) on video frames.
- **`draw_detection()`**: Draws bounding boxes with labels on detected objects.
- **`process_frame()`**: Processes video frames, applying YOLO-based detection.

#### Additional Classes

- **ConveyorSystemController:** Manages Arduino-Python communication, ensuring thread safety.
- **DualMotorSpeedController:** Adjusts motor speeds based on load cell data and smoothing algorithms.

#### Database Management: `shared_data.py`

- Creates and manages SQLite3 tables.
- Provides helper methods for data retrieval and visualization.

#### Dashboard Integration
- **`send_to_dashboard()` & `send_load_to_dashboard()`**: Updates the database and reflects changes on the dashboard.

---

## How to Run the Code

### Prerequisites
- Arduino board connected to the system.
- Two functional cameras. Verify their ports before proceeding.

### Steps
1. Run the `unified_motor_control.py` script.
2. Check the terminal for issues.
3. Launch the dashboard by running `working_dashboard.py`.
4. Open the localhost address displayed in the terminal.

---

## Troubleshooting

### Common Issues
- **Camera Detection:** Verify ports (e.g., 0, 1, 2). Use `cv2.CAPDSHOW` if necessary.
- **Serial Communication:** Ensure correct baud rate (e.g., 9600) and verify hardware connections.
- **Performance Issues:** Optimize threading if cameras fail to open.

---

## Data Resources
Custom data folder link:
[Google Drive Folder](https://drive.google.com/drive/folders/1ldCc5GZ_552SDihetrbSGQCT4nlTKPYk?usp=sharing)

---

This document provides a detailed guide to understanding and executing the speed control system based on area detection. For further assistance, consult the code or contact the project maintainers.