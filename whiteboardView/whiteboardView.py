import socket
import cv2
import numpy as np
import math
import cvHelper
import collections
class border():

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
    #list of coordinates for corners of rectangle. counted for assurance 
    self.potentialBorder = collections.Counter()

    def findBorder(self, img):
        img2 = cvHelper.colorSelect2(img)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        #manage contours somehow??
        _,contours,_ = cv2.findContours(img2,modes[3], methods[0])
        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        box = tuple([tuple(x) for x in box])
        potentialBorder.update(box)

    def borderFound(self):
        mostCommon = portentialBorder.most_common()[0]
        if mostCommon[1] > self.minBorderThreshold:
            self.setBorder(mostCommon)
            return True
        else:
             return false
    
    def setBorder(self, border):
        self.borderboundries = border
        self.origin = sorted(sorted(border)[:2], key = lambda x : x[1])[0]
        point = sorted(sorted(border)[2:], key = lambda x : x[1])[0]
        point2 = sorted(sorted(border)[:2], key = lambda x : x [1])[1]
        self.width = math.sqrt((point[1] - self.origin[1])**2 + (point[0] - self.origin[0])**2)
        self.height = math.sqrt(point2[1] - self.origin[1])**2 + (point2[0] - self.origin[0])**2)
        self.slope = (point[1] - self.origin[1]) / (point[0] - self.origin[0])

    def getPositionOfPoint(self, point):
        #relative x position is intersect formula for line with a perpendicular slope
        a = np.array([[1, -1/self.slope], [1, -self.slope]]) 
        b = np.array([point[1] - (1/self.slope) * point[0] ,self.origin[1] - (self.slope * self.origin[0]))
        xPos = np.linalg.solve(a,b)[0][0]
        #relative y position is intersect formul for line with a the slop as the slope        
        a = np.array([[1, -self.slope], [1, -1/self.slope]]) 
        b = np.array([point[1] - (self.slope) * point[0] ,self.origin[1] - ((1/self.slope) * self.origin[0]))
        yPos = np.linalg.solve(a,b)[0][1]
        return [xPos / self.width, yPos / self.Height]
    


class whiteboard():




    self.sock = None
        

    def connect(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        return self.sock

    def send(self,mesg, sock):
        self.sock.send(str.encode(mesg))
        print(mesg)

    def getPositionAsPercent(self,pos, screen):
        print(pos,screen)
        return (pos[0]/screen[0]*100,pos[1]/screen[1]*100)

    def detectLED(self, video, template):
        #use same method as border template.  if contours are outside current border, ignore
