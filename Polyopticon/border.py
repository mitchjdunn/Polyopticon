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
        self.topslope = 0.0
        self.bottomslope = 0.0
        self.leftslope = 0.0
        self.rightslope = 0.0
        #rectangle dimensions
        self.leftheight = 0
        self.rightheight = 0
        self.topwidth = 0
        self.bottomwidth = 0
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
        self.topwidth = math.sqrt((self.topRight[1] - self.topLeft[1])**2 + (self.topRight[0] - self.topLeft[0])**2)
        self.leftheight = math.sqrt((self.bottomLeft[1] - self.topLeft[1])**2 + (self.bottomLeft[0] - self.topLeft[0])**2)
        self.bottomwidth = math.sqrt((self.bottomRight[1] - self.bottomLeft[1])**2 + (self.bottomRight[0] - self.bottomLeft[0])**2)
        self.rightheight = math.sqrt((self.bottomRight[1] - self.topRight[1])**2 + (self.bottomRight[0] - self.topRight[0])**2)
        #rise over run baby
        self.topslope = float(self.topRight[1] - self.topLeft[1]) / (self.topRight[0] - self.topLeft[0])
        self.bottomslope = float(self.bottomRight[1] - self.bottomLeft[1]) / (self.bottomRight[0] - self.bottomLeft[0])
        self.rightslope = float(self.topRight[1] - self.bottomRight[1]) / (self.topRight[0] - self.bottomRight[0])
        self.leftslope = float(self.topLeft[1] - self.bottomLeft[1]) / (self.topLeft[0] - self.bottomLeft[0])

    def getPositionOfPoint(self, point):

        #get the x value of the point of intersection
        xPosTop = self.lineInterceptForm(point, 1/self.topslope, self.topLeft, self.topslope)[0] 
         # get x position from intercept with bottom line
        xPosBottom = self.lineInterceptForm(point, 1/self.bottomslope, self.bottomLeft, self.bottomslope)[0] 
        #Y position
        # get y position from intercept with left line
        yPosLeft = self.lineInterceptForm(point, 1/self.leftslope, self.topLeft, self.leftslope)[1]
        # get y position from intercept with right line
        yPosRight = self.lineInterceptForm(point, 1/self.rightslope, self.topRight,self.rightslope)[1]

        #normalize -- subtract from the orign
        txavg=abs(xPosTop - self.topLeft[0]) / self.topwidth* 100
        bxavg=abs(xPosBottom - self.topLeft[0]) / self.bottomwidth* 100
        lyavg=abs(yPosLeft - self.topLeft[1]) / self.leftheight* 100
        ryavg=abs(yPosRight - self.topLeft[1]) / self.rightheight* 100
        if self.debug:
            print(xPosTop)
            print(xPosBottom)
            print(yPosLeft)
            print(yPosRight)
            print('txavg:{}'.format(txavg))
            print('bxavg:{}'.format(bxavg))
            print('ryavg:{}'.format(ryavg))
        return [(txavg + bxavg) /2,(lyavg + ryavg) /2]

    def inBorder(self, point):
        p = []
        for x in [-2, 2]:
            for y in [-2, 2]:
                p = Point(point[0] + x, point[1] + y)   
                polygon = Polygon((self.borderboundries[0],self.borderboundries[1],self.borderboundries[2],self.borderboundries[3]))
                if not polygon.contains(p):
                    return False
        return True
    def lineInterceptForm(self,point1, slope1, point2, slope2):
        coefficients = np.array([[-slope1, 1], [-slope2, 1]])
        solutions = np.array([point1[1] - slope1 * point1[0], point2[1] - slope2 * point2[0]])

        intercept = np.linalg.solve(coefficients, solutions)
        return(intercept)
def main():
    from border import Border
    from whiteboardView import cvHelper
    b = Border()
    b.lineInterceptForm((1,0), 3, (1,6.3), 2.3)
    
    
if __name__ == '__main__':
    main()
