from ultralytics import YOLO
import os
import cv2 as cv


url = "http://192.168.44.117:8080/video"

cap = cv.VideoCapture(url)
modelPath = "runs/detect/train3/weights/best.pt"
model = YOLO(modelPath)

while True:
    ret, frame = cap.read()
    if ret:
        frame = cv.flip(frame, 1)
        img = cv.resize(frame, (640, 480))
        results = model(source=img, show=True, conf=0.15)
        for result in results:
            # print(result)
            box = result.boxes

        key = cv.waitKey(1)
        if key == ord("q"):
            break
