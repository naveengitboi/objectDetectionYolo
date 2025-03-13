import cv2 as cv
import numpy as np

def getContours(img, cThr=[80,150], showCanny=False, MINAREA=500, filter=0, draw=False):
    imgGray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # cv.imshow("Canny Img", imgGray)
    imgBlur = cv.GaussianBlur(imgGray, (5, 5), 1)
    # cv.imshow("Blur Img", imgBlur)
    imgCanny = cv.Canny(imgBlur, cThr[0], cThr[1])
    # cv.imshow("Canny Canny", imgCanny)
    imgThreshold = imgCanny.copy()
    if showCanny:
        cv.imshow("Canny Img", imgThreshold)

    contours, hiearchy = cv.findContours(imgThreshold, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    finalContours = []
    for i in contours:
        area = cv.contourArea(i)
        if area > MINAREA:
            perimeter = cv.arcLength(i,True)
            approx = cv.approxPolyDP(i, 0.02 * perimeter, True)
            boundingBox = cv.boundingRect(approx)
            if filter > 0:
                if len(approx) == filter:
                    finalContours.append([len(approx), area,approx,
                                         boundingBox, i])
            else:
                finalContours.append([len(approx), area, approx,
                                     boundingBox, i])
    finalContours = sorted(finalContours, key = lambda x: x[1], reverse=True)
    if draw:
        for cont in finalContours:
            cv.drawContours(img, cont[4],-1, (0, 255, 0), 3)

    return img, finalContours

def reorder(myPoints):
    myPointsNew = np.zeros_like(myPoints)
    myPoints = myPoints.reshape((4, 2))
    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew


def warpImage(img, points, w, h, pad = 3):
    # print("Points in warpFunc ",points)
    # print("Points in warpFunc ", points.shape)
    points = reorder(points)
    pts1 = np.float32(points)
    pts2 = np.float32([[0,0], [w,0], [0,h], [w,h]])
    matrix = cv.getPerspectiveTransform(pts1, pts2)
    # print("Matrix ", matrix)
    imgWarp = cv.warpPerspective(img, matrix, (w, h))
    imgWarp = imgWarp[pad:imgWarp.shape[0] - pad, pad:imgWarp.shape[1] - pad]
    return imgWarp

def findDis(pts1,pts2):
    return ((pts2[0]-pts1[0])**2 + (pts2[1]-pts1[1])**2)**0.5