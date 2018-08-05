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
        self.slope = 0.0
        #rectangle dimensions
        self.height = 0
        self.width = 0
        self.topRight = []
        self.bottomLeft = []
        self.bottomRight = []
        #list of coordinates for corners of rectangle. counted for assurance 
        self.potentialBorder = collections.Counter()
        self.minBorderThreshold = 10

    
    #Takes in image and looks for corner squares for finding border
    #return true if found, false if not
    def findCorner(self,img, descriptor):
        if self.debug:
            print('border.findeCorner')
        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        _,contours,_ = cv2.findContours(img,modes[0], methods[0])



        img1 = cv2.cvtColor(img.copy(), cv2.COLOR_GRAY2BGR)
        if not contours: 
            if self.debug:
                print('no contours')
                return
        contours = sorted(contours, key=lambda x: cv2.arcLength(x, False), reverse=True)
        
        for c in contours:
            poly = cv2.approxPolyDP(c, 25, True)
            print(poly)
                #if not self.inBorder(x):
                #    continue
            
            rect = cv2.minAreaRect(c)
            box= cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.imshow('c', cv2.drawContours(img1, [box], 0, (0,255,255), 3))
            #cv2.waitKey(0)
            box = tuple([tuple([int(x) - int(x) % 2, int(y) - int(y) % 2]) for x,y in box])

            print(box)
            if descriptor is 'topright':
                print('topright')
                print(sorted(sorted(box)[2:], key = lambda x : x[1])[0])
                self.topRight =  sorted(sorted(box)[2:], key = lambda x : x[1])[0]
                return True
            elif descriptor is 'topleft':
                print('topleft')
                print(sorted(sorted(box)[:2], key = lambda x : x[1])[0])
                self.topLeft = sorted(sorted(box)[:2], key = lambda x : x[1])[0]
                return True
            elif descriptor is 'bottomright':
                print('bottomright')
                print(sorted(sorted(box)[2:], key = lambda x : x[1])[1])
                self.bottomRight =sorted(sorted(box)[2:], key = lambda x : x[1])[1] 
                self.setBorder((self.topRight,self.topLeft,self.bottomLeft, self.bottomRight))
                return True
            elif descriptor is 'bottomleft':
                print('bottomleft')
                print(sorted(sorted(box)[:2], key = lambda x : x[1])[1])
                self.bottomLeft=sorted(sorted(box)[:2], key = lambda x : x[1])[1]
                return True
            else:
                print('descriptor invalid')
                return False
            #TODO remove
            img1 = cv2.cvtColor(img.copy(), cv2.COLOR_GRAY2BGR)
            img1 = cv2.drawContours(img1, [poly],-1, (255,0,0), 3)
            #cv2.waitKey(0)
        
        return False
        
    def setBorder(self, border):
        self.borderboundries = border
        self.borderFound = True
        if self.debug:
            print("setborder({})".format(border))
        #get points of rectangle
        #self.topLeft = sorted(sorted(border)[:2], key = lambda x : x[1] )[0]
        #self.topRight = sorted(sorted(border)[2:], key = lambda x : x[1])[0]
        #self.bottomLeft  = sorted(sorted(border)[:2], key = lambda x : x[1])[1]
        #get width height and slope for corner points
        self.width = math.sqrt((self.topRight[1] - self.topLeft[1])**2 + (self.topRight[0] - self.topLeft[0])**2)
        self.height = math.sqrt((self.bottomLeft[1] - self.topLeft[1])**2 + (self.bottomLeft[0] - self.topLeft[0])**2)
        #rise over run baby
        self.slope = float(self.topRight[1] - self.topLeft[1]) / (self.topRight[0] - self.topLeft[0])

    def getPositionOfPoint(self, point):
        #relative x position is intersect formula for line with a perpendicular slope
        a = np.array([[1.0, -1.0/self.slope], [1.0, float(-self.slope)]]) 
        b = np.array([float(point[1]) - (1.0/self.slope) * float(point[0]) ,float(self.topLeft[1] - (self.slope * self.topLeft[0]))])
        #X is equal to the x position of the intersect of the top line and a line from point with a slope perpendicular to the top line.
        xPos = np.linalg.solve(a,b)[1]
        if self.debug:
            print(np.linalg.solve(a,b))
        a = np.array([[1.0, float(-self.slope)], [1.0, -1.0/self.slope]]) 
        b = np.array([float(point[1])   - float(self.slope) * float(point[0]) ,float(self.topLeft[1]) - ((1.0/self.slope) * self.topLeft[0])])
        yPos = np.linalg.solve(a,b)[0]
        if self.debug:
            print(np.linalg.solve(a,b))
            print("topLeft", self.topLeft)
            print("width, height", self.width, self.height)
            print('xpos,ypos', xPos - self.topLeft[0],yPos - self.topLeft[1])
        return [( xPos - self.topLeft[0]) * 100 / self.width , (yPos - self.topLeft[1]) * 100/ self.height ]

    def inBorder(self, point):
        p = []
        for x in [-2, 2]:
            for y in [-2, 2]:
                p = Point(point[0] + x, point[1] + y)   
                polygon = Polygon((self.borderboundries[0],self.borderboundries[1],self.borderboundries[2],self.borderboundries[3]))
                if not polygon.contains(p):
                    return False
        
        return True
#        borderBuffer = 5
#        topLine = (point[0] - self.topLeft[0]) * self.slope + self.topLeft[1] 
#        bottomLine = (point[0] - self.bottomLeft[0]) *  self.slope + self.bottomLeft[1] 
#        leftLine = (point[1] - self.topLeft[1] + self.topLeft[0] / self.slope) * self.slope
#        rightLine = (point[1] - self.topRight[1] + self.topRight[0] / self.slope) * self.slope
#        print("point: ", point, 'topLine: ', topLine, 'bottomLine: ', bottomLine)
#        if point[0] > topLine + borderBuffer and point[0] < bottomLine + borderBuffer and point[1] > leftLine + borderBuffer and point[1] < rightLine - borderBuffer:
#            return True
#
def main():
    from border import Border
    from whiteboardView import cvHelper
    b = Border(debug=True)
    img = cv2.imread('topRight.png')
    img = cvHelper.colorSelect(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b.findCorner(img,'topright')
    img = cv2.imread('topLeft.png')
    img = cvHelper.colorSelect(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b.findCorner(img,'topleft')
    img = cv2.imread('bottomRight.png')
    img = cvHelper.colorSelect(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b.findCorner(img,'bottomright')
    img = cv2.imread('bottomLeft.png')
    img = cvHelper.colorSelect(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b.findCorner(img,'bottomleft')
if __name__ == '__main__':
    main()
