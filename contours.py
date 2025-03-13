import utils
import cv2 as cv
import numpy as np


def contoursFile():
    img, contours = utils.getContours(frame, draw=False, filter=4, cThr=[100,150])
    if len(contours) != 0:
        biggest = contours[0][2]
        # print("biggest shape",biggest)
        imgWarp = utils.warpImage(img, biggest, WidthOfConveyor, LengthOfConveyor)
        imgContours2, conts2 = utils.getContours(imgWarp, draw=False, filter=4, cThr=[100,150])

        if len(conts2) != 0:
            for obj in conts2:
                cv.polylines(imgContours2,[obj[2]],True,(0,255,0),2)
                nPoints = utils.reorder(obj[2])
                newWidth = round(utils.findDis(nPoints[0][0]//scaleFactor, nPoints[1][0]//scaleFactor)/10,1)
                newHeight = round(utils.findDis(nPoints[0][0] // scaleFactor, nPoints[1][0] // scaleFactor)/10,1)
                cv.arrowedLine(imgContours2, (nPoints[0][0][0], nPoints[0][0][1]),
                                (nPoints[1][0][0], nPoints[1][0][1]),
                                (255, 0, 255), 3, 8, 0, 0.05)
                cv.arrowedLine(imgContours2, (nPoints[0][0][0], nPoints[0][0][1]),
                                (nPoints[2][0][0], nPoints[2][0][1]),
                                (255, 0, 255), 3, 8, 0, 0.05)
                x, y, w, h = obj[3]
                cv.putText(imgContours2, '{}cm'.format(newWidth), (x + 30, y - 10), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5,
                            (255, 0, 255), 2)
                cv.putText(imgContours2, '{}cm'.format(newHeight), (x - 70, y + h // 2), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5,
                            (255, 0, 255), 2)
        # cv.imshow('imgWarp', imgContours2)