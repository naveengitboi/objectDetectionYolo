from ultralytics import YOLO
from ultralytics.solutions import object_counter
import os, time
import cv2 as cv
import cvzone
import math
from sort import *
import utils
from arduinoFile import MotorController


url = "http://192.168.44.117:8080/video"
PORT = "COM5"
BRate = 9600
MIN_SPEED = 100  # Minimum motor speed (steps per second)
MAX_SPEED = 800  # Maximum motor speed (steps per second)
MAX_COUNT = 100  # Maximum expected object count
MAX_AREA = 1000  # Maximum expected total area of objects
WEIGHT_COUNT = 0.4  # Weight for object count in the calculation
WEIGHT_AREA = 0.6  # Weight for area in the calculation

sFactor = 1

scaleFactor = 2
WidthOfConveyor = 1080
LengthOfConveyor = 1080

print("Camera Setup Started")

cap = cv.VideoCapture(0,cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 1200)

print("Camera Setup Initialized")


#arduino intialization
print("Controller Setup Initialized")
motor_controller = MotorController(PORT, BRate)


#best.pt model of yolov8n (nano)
print("Waiting to connect Model....")
modelPath = "runs/detect/train3/weights/best.pt"
model = YOLO(modelPath)
print("Model Initialized....")
# currentDirecotry = os.getcwd()

counter = object_counter.ObjectCounter()
coords = [topLeft,topRight, bottomRight, bottomLeft] = [(0,0), (1920,0), (1920,1080), (0,1080)]
regionPoints = coords

tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)

lx, ly, rx, ry = [450,152,600,152]
lineCoords = [lx, ly, rx, ry]
totalObjCounts = []

# conveyor coordenates
cx1, cy1, cx2, cy2 =[140, 0, 850, 1200]


def liesInsideTheBox(x1, y1, x2, y2,cx1, cy1, cx2, cy2):
     if x1 >= cx1 and x2 <= cx2 and y1 >= cy1 and y2 <= cy2:
         return True
     return False

# linear interpolation for speed
def lerp(minSpeed, maxSpeed , speedFactor):
    return (maxSpeed-minSpeed)*speedFactor + minSpeed

classNames = ['typeOne', 'typeTwo', 'typeThree', 'typeFour']

def getRangeSpeedOfMotor(speed):
    lowVal = speed//100
    midVal = lowVal*100 + (lowVal+1)*10
    return midVal
def calculate_speed(object_count, total_area):
    # Normalize the inputs
    normalized_count = object_count / MAX_COUNT
    normalized_area = total_area / MAX_AREA

    # Combine the factors with weights
    factor = (WEIGHT_COUNT * normalized_count + WEIGHT_AREA * normalized_area) / (WEIGHT_COUNT + WEIGHT_AREA)
    print("Factor idk what it is, ", factor)
    # Calculate speed using linear interpolation
    speed = lerp(MIN_SPEED, MAX_SPEED, factor)
    print("Speed in function ", speed)
    speed = getRangeSpeedOfMotor(speed)
    print("Speed after ranged ", speed)
    return int(speed)




while True:
    ret, img = cap.read()
    if not ret:
        print("Not connected")
        continue
    img = cv.flip(img, 1)
    frame = img

    results = model.predict(source=frame,stream=True, conf=0.035)

    totalArea = 0

    detections = np.empty((0,5))

    cv.rectangle(frame, (cx1, cy1), (cx2, cy2), (255, 0, 0), 3)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            color = (255,0,255)
            width, height = x2-x1, y2-y1
            boundingBox = (x1, y1, width, height)
            if liesInsideTheBox(x1, y1, x2, y2,cx1, cy1, cx2, cy2):
                cvzone.cornerRect(frame, boundingBox, cv.LINE_AA)

                confidence = math.ceil((box.conf[0]*100))/100
                positionOfText = (max(0, x1), max(35,y1))
                posOfAreaText = (max(0, x2), max(35, y2))

                area = math.floor(int(width*height)/1820)
                totalArea += area
                cls = int(box.cls[0])
                cvzone.putTextRect(frame, f'{classNames[cls]} {confidence}', positionOfText,
                                   scale=2, thickness=1, offset=5)
                currentArray = np.array([x1,y1,x2,y2, confidence])

                cvzone.putTextRect(frame, f'{area} cm2',posOfAreaText, scale=2, thickness=1, offset=5)
                detections = np.vstack([detections, currentArray])

    cvzone.putTextRect(frame, f'Area {totalArea} cm2', (0,50), scale=2, thickness=1, offset=5)



    trackerResults = tracker.update(detections)
    cv.line(frame, (lineCoords[0], lineCoords[1]), (lineCoords[2], lineCoords[3]),
            (0,0,255), 2)
    for tResult in trackerResults:
        x1, y1, x2, y2, id = tResult
        x1, y1, x2, y2, id = int(x1), int(y1), int(x2), int(y2), int(id)
        w, h = x2-x1 , y2-y1
        # cvzone.putTextRect()

        cx, cy = x1 + w//2 , y1+ h//2

        if liesInsideTheBox(x1, y1, x2, y2, cx1, cy1, cx2, cy2):
            if id not in totalObjCounts:
                totalObjCounts.append(id)

    #object counts crosed that line
    countedObjects = len(totalObjCounts)
    speedOfMotor = calculate_speed(countedObjects, totalArea)
    # print("Speed of Motor currently is, ", speedOfMotor)
    if speedOfMotor:
        motor_controller.set_speed(speedOfMotor * sFactor, min_delay=5)

    else:
        motor_controller.set_speed(500, min_delay=5)


    cvzone.putTextRect(frame, f'#of {countedObjects}',(300,50), scale=2)
    cvzone.putTextRect(frame, f'speed of motor  {speedOfMotor}', (400, 50), scale=2)

    cv.imshow("Results", frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break







