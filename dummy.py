import cv2 as cv

print("Struggling, ")



cap = cv.VideoCapture(1)

while True:
    ret, frame = cap.read()
    frame = cv.flip(frame, 1)
    cv.imshow('frame', frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break