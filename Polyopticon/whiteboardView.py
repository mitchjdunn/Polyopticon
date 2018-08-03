from time import sleep
import cv2
import numpy as np
import math
from whiteboard import Paint
from border import Border

class cvHelper:

    def colorSelect2(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_white = np.array([0,0,200])
         upper_white = np.array([240,80,255])
         mask = cv2.inRange(hsv, lower_white, upper_white)
         return cv2.bitwise_and(img,img, mask= mask)

class Whiteboard:


    def __init__(self, whiteboard):
        self.p = whiteboard
        self.border = None
        self.debug = False
        self.prod = False
        self.penDown = False
        self.lastPen = None
        self.readyMessageSent = False


        #Socket for video stream
        self.videosocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def up(self):
        self.penDown = False
        self.p.handle('up') 
    def down(self, pos):
        self.penDown = True
        self.p.handle("down," + str(pos[0]) + ',' + str(pos[1]))
    def newLEDPos(self, pos):
        self.lastPen = pos
        self.p.handle(str(pos[0]) +','+str(pos[1]))
        #draw

    def nextFrame(self, img):
        if self.debug:
            print("next Frame")
        #CHECKING FOR BORDER
        if self.border is None:
            self.border = Border()
            if self.prod:
                pass
                #TODO handle calibration
                #self.send('calibrating')
        if not self.border.borderFound:
            #CHANGE IMG BEFORE FINDBORDER
            #img1 = Whiteboard.colorSelect(img.copy())
            img1 = cvHelper.colorSelect2(img.copy())
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            self.border.findBorder(img1)

            if self.debug:
                print(self.border.potentialBorder)
            return

        if not self.readyMessageSent and self.prod:
            self.readyMessageSent = True
            #TODO handle ready message
            #self.send('ready')
            
        if self.debug:
        #SHOW BORDER
            box = np.int0(self.border.borderboundries)
            img2 = img.copy()
            img2 = cv2.drawContours(img2, [box], 0,(0,0,255), 2)
        
        #CHECKING FOR LED
        #img1 = Whiteboard.colorSelect(img.copy())
        img1 = cvHelper.colorSelect2(img.copy())
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        LED = self.detectLED(img1)
        if LED is not None:
            LEDx, LEDy = self.border.getPositionOfPoint(LED)
            if self.debug:
                img2 = cv2.circle(img2, LED, 5, (0,255,0), 2)
                print((LEDx, LEDy))
            if self.prod:
                if self.penDown:
                    #checking distance between pen strokes -- don't want misfires to draw lines
                    if self.lastPen is not None:
                        if abs(self.lastPen[0] - LEDx) > 5 or abs(self.lastPen[1] - LEDy) > 5:
                            self.up()
                            self.down((LEDx, LEDy))
                    self.newLEDPos((LEDx,LEDy))
                else:
                    self.down((LEDx, LEDy))
        else:
            if self.debug:
                print('No LED')
            if self.prod:
                if self.penDown:
                    self.up()

        if self.debug:
            cv2.imshow('img', img)
            cv2.imshow('img2', img2)
    def runVideo(self, videoPath):
        self.

        
        if self.debug:
            print("runVideo")
        cap = cv2.VideoCapture(videoPath)

        ret, img = cap.read()
        if not ret and self.debug:
            print("no video")
        while ret:
            self.nextFrame(img)
            print("hiya")
            cv2.waitKey(1)
            ret, img = cap.read()

    def detectLED(self, img):

        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        #manage contours somehow??
        _,contours,_ = cv2.findContours(img,modes[1], methods[0])
        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        box = tuple([tuple(x) for x in box])
        if self.debug:
            print('og box: ', box)
        topRight = sorted(sorted(box)[2:], key = lambda x : x[1])[0]
        bottomLeft  = sorted(sorted(box)[:2], key = lambda x : x [1])[1]
        if self.debug:
            print('new box', box)
        #find cener of box
        x,y = (int((topRight[0] + bottomLeft[0]) / 2),int((topRight[1] + bottomLeft[1]) / 2))
        if self.border.inBorder((x,y)):
            return (int((topRight[0] + bottomLeft[0]) / 2),int((topRight[1] + bottomLeft[1]) / 2))
        return None

def main():
    p = Paint(master = True)
    p.setup()
    #Get host from network discovery.
    while not p.slaveAttached:
        print("slave not found")
        sleep(1)
    host = p.slaveIP
    #host = "192.168.1.6"
    print(host)
    #port = '4545'
    w = Whiteboard(p)
    w.debug = True
    w.prod = False
    #w.runVideo("udp://@" + host + ":" + port)

if __name__ == '__main__':
    main()
