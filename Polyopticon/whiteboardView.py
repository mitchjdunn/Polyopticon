import socket
import time
import cv2
import numpy as np
import math
from border import Border

class cvHelper:

    def colorSelect2(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_white = np.array([0,0,200])
         upper_white = np.array([240,80,255])
         mask = cv2.inRange(hsv, lower_white, upper_white)
         return cv2.bitwise_and(img,img, mask= mask)

class Whiteboard:


    def __init__(self):

        self.border = None
        self.sock = socket.socket()
        self.debug = False
        self.prod = False
        self.penDown = False
        self.lastPen = None
        self.readyMessageSent = False
        

    def connect(self, host, port):
        print('connect',host,port)
        self.sock.connect((host, port))

    def send(self,mesg):
        self.sock.send(str.encode(mesg +"\n"))
        print(mesg)
        return

    def nextFrame(self, img):
        if self.debug:
            print("next Frame")
        #CHECKING FOR BORDER
        if self.border is None:
            self.border = Border()
            if self.prod:
                self.send('calibrating')
        if not self.border.borderFound:
            #CHANGE IMG BEFORE FINDBORDER
            img1 = Whiteboard.colorSelect(img.copy())
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            self.border.findBorder(img1)

            if self.debug:
                print(self.border.potentialBorder)
            return

        if not self.readyMessageSent and self.prod:
            self.readyMessageSent = True
            self.send('ready')
            
        if self.debug:
        #SHOW BORDER
            box = np.int0(self.border.borderboundries)
            img2 = img.copy()
            img2 = cv2.drawContours(img2, [box], 0,(0,0,255), 2)
        
        #CHECKING FOR LED
        img1 = Whiteboard.colorSelect(img.copy())
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
                        if abs(self.lastPen[0] - LEDx) > .1 or abs(self.lastPen[1] - LEDy) > .1:
                            self.send('up')
                            self.send('down' + str(LEDx) + ',' + str(LEDy))
                    self.send(str(LEDx) + ',' + str(LEDy))
                else:
                    self.penDown = True
                    self.send("down," + str(LED[0]) + ',' + str(LED[1]))
        else:
            if self.debug:
                print('No LED')
            if self.prod:
                if self.penDown:
                    self.penDown = False
                    self.send('up')

        if self.debug:
            cv2.imshow('img', img)
            cv2.imshow('img2', img2)
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
    w = Whiteboard()
    #Get host from network discovery.
    host = 'jon-laptop'
    port = 15273
    w.debug = True
    w.prod = False
    if w.prod:
        connected = False
        while not connected:
            try:
                w.connect(host, port)
                connected = True

            except Exception as e:
                print('not connected')
                time.sleep(1)
                pass
    w.runVideo('tests/piTests/vid/demotest-20s--4-full.mp4')
    #w.runVideo("udp://" + host + ":" + port)

if __name__ == '__main__':
    main()