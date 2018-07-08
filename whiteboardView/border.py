import socket
import cv2
import numpy as np
import math
from cvHelper import cvHelper 
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import collections
class Border:

    def __init__(self):
        self.debug = False
        #Final variables
        #minimum amount of times a rectangle is found before it becomes the border
        self.minBorderThreshold = 10
            
        self.borderFound = False
        #confirmed border corners
        self.borderboundries = []
        #top left corner of the rectangle.  relative coordinates are  (0,0)
        self.origin = []
        #slope of the top line of the rectangle.  Used for relative positioning of the LED
        self.slope = 0
        #rectangle dimensions
        self.height = 0
        self.width = 0
        self.topRight = []
        self.bottomLeft = []
        #list of coordinates for corners of rectangle. counted for assurance 
        self.potentialBorder = collections.Counter()

    def findBorder(self, img):
        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        #manage contours somehow??
        _,contours,_ = cv2.findContours(img,modes[3], methods[0])
        rect = cv2.minAreaRect(contours[0])
        if rect is None:
            if self.debug:
                print("no rectangle")
            return
        box = cv2.boxPoints(rect)
        box = tuple([tuple([int(x), int(y)]) for x,y in box])
        if self.debug:
            print(box, "Box")
        width, height = img.shape[:2]
        if (abs(box[0][0] - box[1][0]) > width / 4 or abs(box[0][0] - box[2][0]) > width/4) and (abs(box[0][1] - box[1][1]) > height/4 or abs(box[0][1] - box[2][1]) > height/4):
            self.potentialBorder.update((box,))
        if self.debug:
            print(self.potentialBorder)
        if len(self.potentialBorder) == 0:
            return 
        border = self.potentialBorder.most_common(1)[0]
        if  border[1] >= self.minBorderThreshold:
            self.setBorder(border[0])

#    def borderFound(self):
#        mostCommon = self.potentialBorder.most_common()
#        if self.debug:
#            print(mostCommon)
#        if len(mostCommon) is not 0 and mostCommon[0][1] > self.minBorderThreshold:
#            
#            return True
#        else:
#            return False
    
    def setBorder(self, border):
        self.borderboundries = border
        self.borderFound = True
        if self.debug:
            print("border")
            print(border)
        self.origin = sorted(sorted(border)[:2], key = lambda x : x[1])[0]
        self.topRight = sorted(sorted(border)[2:], key = lambda x : x[1])[0]
        self.bottomLeft  = sorted(sorted(border)[:2], key = lambda x : x [1])[1]
        self.width = math.sqrt((self.topRight[1] - self.origin[1])**2 + (self.topRight[0] - self.origin[0])**2)
        self.height = math.sqrt((self.bottomLeft[1] - self.origin[1])**2 + (self.bottomLeft[0] - self.origin[0])**2)
        self.slope = (self.topRight[1] - self.origin[1]) / (self.topRight[0] - self.origin[0])

    def getPositionOfPoint(self, point):
        #relative x position is intersect formula for line with a perpendicular slope
        a = np.array([[1, -1/self.slope], [1, -self.slope]]) 
        b = np.array([point[1] - (1/self.slope) * point[0] ,self.origin[1] - (self.slope * self.origin[0])])
        xPos = np.linalg.solve(a,b)[1]
        if self.debug:
            print(np.linalg.solve(a,b))
        a = np.array([[1, -self.slope], [1, -1/self.slope]]) 
        b = np.array([point[1]   - (self.slope) * point[0] ,self.origin[1] - ((1/self.slope) * self.origin[0])])
        yPos = np.linalg.solve(a,b)[0]
        if self.debug:
            print(np.linalg.solve(a,b))
            print("origin", self.origin)
            print("width, height", self.width, self.height)
            print('xpos,ypos', xPos - self.origin[0],yPos - self.origin[1])
        return [( xPos - self.origin[0]) * 100 / self.width , (yPos - self.origin[1]) * 100/ self.height ]

    def inBorder(self, point):
        p = Point(point[0], point[1])
        print(self.borderboundries)
        polygon = Polygon((self.borderboundries[0],self.borderboundries[1],self.borderboundries[2],self.borderboundries[3]))
        return polygon.contains(p)
#        borderBuffer = 5
#        topLine = (point[0] - self.origin[0]) * self.slope + self.origin[1] 
#        bottomLine = (point[0] - self.bottomLeft[0]) *  self.slope + self.bottomLeft[1] 
#        leftLine = (point[1] - self.origin[1] + self.origin[0] / self.slope) * self.slope
#        rightLine = (point[1] - self.topRight[1] + self.topRight[0] / self.slope) * self.slope
#        print("point: ", point, 'topLine: ', topLine, 'bottomLine: ', bottomLine)
#        if point[0] > topLine + borderBuffer and point[0] < bottomLine + borderBuffer and point[1] > leftLine + borderBuffer and point[1] < rightLine - borderBuffer:
#            return True
#
