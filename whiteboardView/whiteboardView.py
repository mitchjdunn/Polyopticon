import socket
import cv2
import numpy as np
import math
from cvHelper import cvHelper 
import collections
class Border:

    def __init__(self):
        self.debug = True
        #Final variables
        #minimum amount of times a rectangle is found before it becomes the border
        self.minBorderThreshold = 10
            
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
        box = tuple([tuple(x) for x in box])
        print(box, "Box")
        if (abs(box[0][0] - box[1][0]) > 600 or abs(box[0][0] - box[2][0]) > 600) and (abs(box[0][1] - box[1][1]) > 300 or abs(box[0][1] - box[2][1]) > 300):
            self.potentialBorder.update((box,))
            print(self.potentialBorder)
            border = self.potentialBorder.most_common(1)[0]
            if  border[1] <= self.minBorderThreshold:

                self.setBorder(border[0])

    def borderFound(self):
        mostCommon = self.potentialBorder.most_common()
        print(mostCommon)
        if len(mostCommon) is not 0 and mostCommon[0][1] > self.minBorderThreshold:
            return True
        else:
             return False
    
    def setBorder(self, border):
        self.borderboundries = border
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
        xPos = np.linalg.solve(a,b)[0][0]
        #relative y position is intersect formul for line with a the slop as the slope        
        a = np.array([[1, -self.slope], [1, -1/self.slope]]) 
        b = np.array([point[1]   - (self.slope) * point[0] ,self.origin[1] - ((1/self.slope) * self.origin[0])])
        yPos = np.linalg.solve(a,b)[0][1]
        return [xPos / self.width, yPos / self.Height]

    def inBorder(self, point):
        topLine = (point[1] - self.origin[1] + self.origin[0] * self.slope) / self.slope
        bottomLine = (point[1] - self.bottomLeft[1] + self.bottomLeft[0] * self.slope) / self.slope
        leftLine = (point[0] - self.origin[0]) / self.slope + self.origin[1]
        rightLine = (point[0] - self.topRight[0]) / self.slope + self.topRight[1]
        if point[0] > topLine and point[0] < bottomLine and point[1] > leftLine and point[1] < rightLine:
            return True

        return False
    


class Whiteboard:


    def __init__(self):

        self.border = None
        self.sock = None
        self.debug = True
        

    def connect(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        return self.sock

    def send(self,mesg, sock):
        self.sock.send(str.encode(mesg))
        print(mesg)
        return


    def nextFrame(self, img):
        if self.debug:
            print("next Frame")
        #CHECKING FOR BORDER
        if self.border is None:
            self.border = Border()
            cv2.imshow('nathin',img)
            return
        if not self.border.borderFound():
            #CHANGE IMG BEFORE FINDBORDER
            img2 = cvHelper.colorSelect2(img)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            self.border.findBorder(img2)
            cv2.imshow('nathin2', img)
            print(self.border.potentialBorder)
            return
            
        #SHOW BORDER
        box = np.int0(self.border.borderboundries)
        cv2.imshow("border", cv2.drawContours(img, [box], 0,(0,0,255), 2))
        
        
        #CHECKING FOR LED
        img2 = cvHelper.colorSelect2(img)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        LED = self.detectLED(img2)
        if LED is not None:
            cv2.imshow("LED", cv2.circle(img,LED, 5, (255,0,0), 1))

    def runVideo(self, videoPath):
        if self.debug:
            print("runVideo")
        cap = cv2.VideoCapture(videoPath)

        ret, img = cap.read()
        if not ret and self.debug:
            print("no video")
        while ret:
            self.nextFrame(img)
            cv2.waitKey()

    def detectLED(self, img):

        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        #manage contours somehow??
        _,contours,_ = cv2.findContours(img,modes[1], methods[0])
        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        box = tuple([tuple(x) for x in box])
        topRight = sorted(sorted(box)[2:], key = lambda x : x[1])[0]
        bottomLeft  = sorted(sorted(box)[:2], key = lambda x : x [1])[1]
        print(box)
        if self.border.inBorder(((topRight[0] + bottomLeft[0]) / 2,(topRight[1] + bottomLeft[1]) / 2)):
            return (int((topRight[0] + bottomLeft[0]) / 2),int((topRight[1] + bottomLeft[1]) / 2))
        return None
        #use same method as border template.  if contours are outside current border, ignore

w = Whiteboard()
w.runVideo('tests/piTests/vid/demotest-20s--4-full.mp4')
