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


# totalArea = 0
#         tAreaRead = 0
#         for result in results:
#             for box in result.boxes:
#                 print(box)
#                 [x1, y1, x2, y2] = box.xyxy[0]
#                 [x_, y_, w, h] = box.xywhn[0]
#                 tAreaRead += w*h
#                 x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#                 print("sizes ",[x1, y1, x2, y2])
#                 w = y2-y1
#                 h = x2-x1
#                 totalArea += w*h
#
#         print("T Area one", totalArea)
#         print("T Area two",tAreaRead)