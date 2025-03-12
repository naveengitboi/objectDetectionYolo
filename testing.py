from ultralytics import YOLO
import os
import cv2 as cv
import serial


url = "http://192.168.44.117:8080/video"

# camera testing and it turned out to be port 1 for webcam
# for i in range(1,7):
#     cap = cv.VideoCapture(i)
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to capture frame", i)
#     else:
#         print("Captured frame", i)
#         while True:
#             ret, frame = cap.read()
#             cv.imshow("frame", frame)
#             if cv.waitKey(1) & 0xFF == ord('q'):
#                 break



cap = cv.VideoCapture(1)
modelPath = "runs/detect/train3/weights/best.pt"
model = YOLO(modelPath)

# linear interpolation
def lerp(A, B , t):
    return (B-A)*t + A

PORT = "COM8"
BRate = 115200
MINSPEED = 0.5
MAXSPEED = 3.0
def communicateWithArduino(seed):
    arduino = serial.Serial(port=PORT, baudrate=BRate, timeout=0.1)
    speed = lerp(MINSPEED, MAXSPEED, seed)
    print("Speed ",speed)
    arduino.write(bytes(speed, 'utf-8'))


while True:
    ret, frame = cap.read()
    if not ret:
        print("Not connected")
        continue
    if ret:
        frame = cv.flip(frame, 1)
        frame = cv.resize(frame, (640, 480))
        coloredFrame = frame

        # gray color
        grayFrame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # threshold Color
        threshFrame = cv.threshold(grayFrame, 60, 255, cv.THRESH_BINARY)[1]
        results = model.predict(source=frame, show=True, conf=0.05)
        cv.imshow( "Threshold Frame", threshFrame)
        cv.imshow( "Gray Frame", grayFrame)
        # cv.imshow("Colored Frame", coloredFrame)

        totalArea = 0
        for result in results:
            # print(result)
            for box in result.boxes:
                [x1, y1, x2, y2] = box.xyxy[0]

                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                print("sizes ",[x1, y1, x2, y2])
                w = y2-y1
                h = x2-x1
                totalArea += w*h
            print(result)
        # print(totalArea)


        if cv.waitKey(1) & 0xFF == ord('q'):
            break
