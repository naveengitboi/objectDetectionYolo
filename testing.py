from ultralytics import YOLO
from ultralytics.solutions import object_counter
import os
import cv2 as cv
import serial
import cvzone
import math


url = "http://192.168.44.117:8080/video"
PORT = "COM8"
BRate = 115200
MINSPEED = 0.5
MAXSPEED = 3.0


cap = cv.VideoCapture(1)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)
# tracking and counting objects


modelPath = "runs/detect/train3/weights/best.pt"

model = YOLO(modelPath)

counter = object_counter.ObjectCounter()
coords = [topLeft,topRight, bottomRight, bottomLeft] = [(0,0), (1920,0), (1920,1080), (0,1080)]
regionPoints = coords
# counter.set_args(view_img = True, reg_pts = regionPoints, class_names = model.names, draw_tracks=True)

# linear interpolation
def lerp(A, B , t):
    return (B-A)*t + A


def communicateWithArduino(seed):
    arduino = serial.Serial(port=PORT, baudrate=BRate, timeout=0.1)
    speed = lerp(MINSPEED, MAXSPEED, seed)
    print("Speed ",speed)
    arduino.write(bytes(speed, 'utf-8'))

classNames = ['typeOne', 'typeTwo', 'typeThree', 'typeFour']



while True:
    ret, img = cap.read()
    if not ret:
        print("Not connected")
        continue
    if ret:
        img = cv.flip(img, 1)
        frame = img
        coloredFrame = frame

        # gray color
        grayFrame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # threshold Color
        threshFrame = cv.threshold(grayFrame, 60, 255, cv.THRESH_BINARY)[1]

        results = model.predict(source=frame,stream=True, conf=0.05)
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                color = (255,0,255)
                boundingBox = (x1, y1, x2-x1, y2-y1)
                cvzone.cornerRect(frame, boundingBox, cv.LINE_AA)

                confidence = math.ceil((box.conf[0]*100))/100
                positionOfText = (max(0, x1), max(35,y1))


                cls = int(box.cls[0])
                print(cls)
                cvzone.putTextRect(frame, f'{classNames[cls]} {confidence}', positionOfText, scale=1.5, thickness=1)



        cv.imshow("Results", frame)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break







