import socket
import cv2
import numpy as np
import math
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import collections
class Border:

    def __init__(self, debug =False):
        self.debug = debug
        if self.debug:
            print('Border init')
        #Final variables
        #minimum amount of times a rectangle is found before it becomes the border
            
        self.borderFound = False
        #confirmed border corners
        self.borderboundries = []
        #top left corner of the rectangle.  relative coordinates are  (0,0)
        self.topLeft = []
        #slope of the top line of the rectangle.  Used for relative positioning of the LED
        self.slope = 0
        #rectangle dimensions
        self.height = 0
        self.width = 0
        self.topRight = []
        self.bottomLeft = []
        #list of coordinates for corners of rectangle. counted for assurance 
        self.potentialBorder = collections.Counter()
        self.minBorderThreshold = 10

    def findBorder(self, img):
        if self.debug:
            print('border.findBorder')

        #cv contour specifics
        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        _,contours,_ = cv2.findContours(img,modes[0], methods[0])

        if not contours:
            if self.debug:
                print('not enough contours')
            return

        #sort contours largest to small
        contours = sorted(contours, key=lambda x: cv2.arcLength(x, False), reverse=True)


        
        #Smallest rectangle containing the largest contour
        rect = cv2.minAreaRect(contours[0])
        if rect is None:
            if self.debug:
                print("no rectangle")
            return
        #set of points
        box = cv2.boxPoints(rect)
        #set of points rounded to the nearest 5 to remove slight variance
        box = tuple([tuple([int(x) - int(x) % 5, int(y) - int(y) % 5]) for x,y in box])
        if self.debug:
            print(box, "Box")
            #img1 = cv2.cvtColor(img.copy(), cv2.COLOR_GRAY2BGR)
            #img1 = cv2.drawContours(img1, [np.int0(box)], 0,(0,0,255),2)
            #cv2.imshow('potentialBox', img1)
        width, height = img.shape[:2]
        #checking size of contour --- if it's two small it wont be accepted
        if (abs(box[0][0] - box[1][0]) > width / 4 or abs(box[0][0] - box[2][0]) > width/4) and (abs(box[0][1] - box[1][1]) > height/4 or abs(box[0][1] - box[2][1]) > height/4):
            self.potentialBorder.update((box,))
        if self.debug:
            print(self.potentialBorder)
        if len(self.potentialBorder) == 0:
            return 
        #Set the border if it has more than 10 counts
        border = self.potentialBorder.most_common(1)[0]
        if  border[1] >= self.minBorderThreshold:
            self.setBorder(border[0])

#    def borderFound(self):
#        mostCommon = self.potentialBorder.most_common()
#        if self.debug:
#            print(mostCommon)
#        if len(mostCommon) is not 0 and mostCommon[0][1] > minBorderThreshold:
#            
#            return True
#        else:
#            return False
    
    def setBorder(self, border):
        self.borderboundries = border
        self.borderFound = True
        if self.debug:
            print("setborder({})".format(border))
        #get points of rectangle
        self.topLeft = sorted(sorted(border)[:2], key = lambda x : x[1])[0]
        self.topRight = sorted(sorted(border)[2:], key = lambda x : x[1])[0]
        self.bottomLeft  = sorted(sorted(border)[:2], key = lambda x : x [1])[1]
        #get width height and slope for cornter points
        self.width = math.sqrt((self.topRight[1] - self.topLeft[1])**2 + (self.topRight[0] - self.topLeft[0])**2)
        self.height = math.sqrt((self.bottomLeft[1] - self.topLeft[1])**2 + (self.bottomLeft[0] - self.topLeft[0])**2)
        #rise over run baby
        self.slope = (self.topRight[1] - self.topLeft[1]) / (self.topRight[0] - self.topLeft[0])

    def getPositionOfPoint(self, point):
        #relative x position is intersect formula for line with a perpendicular slope
        a = np.array([[1, -1/self.slope], [1, -self.slope]]) 
        b = np.array([point[1] - (1/self.slope) * point[0] ,self.topLeft[1] - (self.slope * self.topLeft[0])])
        #X is equal to the x position of the intersect of the top line and a line from point with a slope perpendicular to the top line.
        xPos = np.linalg.solve(a,b)[1]
        if self.debug:
            print(np.linalg.solve(a,b))
        a = np.array([[1, -self.slope], [1, -1/self.slope]]) 
        b = np.array([point[1]   - (self.slope) * point[0] ,self.topLeft[1] - ((1/self.slope) * self.topLeft[0])])
        yPos = np.linalg.solve(a,b)[0]
        if self.debug:
            print(np.linalg.solve(a,b))
            print("topLeft", self.topLeft)
            print("width, height", self.width, self.height)
            print('xpos,ypos', xPos - self.topLeft[0],yPos - self.topLeft[1])
        return [( xPos - self.topLeft[0]) * 100 / self.width , (yPos - self.topLeft[1]) * 100/ self.height ]

    def inBorder(self, point):
        p = Point(point[0], point[1])
        polygon = Polygon((self.borderboundries[0],self.borderboundries[1],self.borderboundries[2],self.borderboundries[3]))
        return polygon.contains(p)
#        borderBuffer = 5
#        topLine = (point[0] - self.topLeft[0]) * self.slope + self.topLeft[1] 
#        bottomLine = (point[0] - self.bottomLeft[0]) *  self.slope + self.bottomLeft[1] 
#        leftLine = (point[1] - self.topLeft[1] + self.topLeft[0] / self.slope) * self.slope
#        rightLine = (point[1] - self.topRight[1] + self.topRight[0] / self.slope) * self.slope
#        print("point: ", point, 'topLine: ', topLine, 'bottomLine: ', bottomLine)
#        if point[0] > topLine + borderBuffer and point[0] < bottomLine + borderBuffer and point[1] > leftLine + borderBuffer and point[1] < rightLine - borderBuffer:
#            return True
#
