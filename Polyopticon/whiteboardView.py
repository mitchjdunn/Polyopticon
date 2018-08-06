from time import sleep
import cv2
import threading
import socket
import numpy as np
import math
import io
import struct
from border import Border

class cvHelper:

    #color select white
    def colorSelect(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_white = np.array([0,0,245])
         upper_white = np.array([255,15,255])
         mask = cv2.inRange(hsv, lower_white, upper_white)
         return cv2.bitwise_and(img,img, mask= mask)
    #color select blue
    def colorSelect2(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_blue = np.array([80,80,180])
         upper_blue = np.array([130,255,255])
         mask = cv2.inRange(hsv, lower_blue, upper_blue)
        # cv2.imshow('colorSelect2', cv2.bitwise_and(img,img, mask= mask))
         return cv2.bitwise_and(img,img, mask= mask)
    def addEdges(img):
        edges = cv2.Canny(img,80,40)
        img = cv2.addWeighted(img, .7, edges, .3,0)
        return img


class WhiteboardView:


    def __init__(self, whiteboard, debug=False, prod=False):
        self.p = whiteboard
        self.upcount=0
        self.debug = debug
        self.prod = prod
        self.border = None
        self.penDown = False
        self.lastPen = None
        self.calibrating = False
        self.framesToSkip = 5
        self.corners = 0
        self.video = False
        self.ports = [4545,4546,4547,4548]
        self.s = socket.socket()


        #Socket for video stream
        self.videosocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        sleep(2)
        for port in self.ports:
            try:
                if self.debug:
                    print((self.p.slaveIP, port)) 
                self.s.connect((self.p.slaveIP, port))
                return
            except:
                print('port {} failed'.format(port))
                pass
        raise SystemError('failed to connect to all ports')

    def up(self):
        self.penDown = False
        self.p.handle('up') 
        self.upcount=0

    def down(self, pos):
        self.upcount=0
        self.penDown = True
        self.p.handle("down," + str(pos[0]) + ',' + str(pos[1]))

    def newLEDPos(self, pos):
        self.lastPen = pos
        self.p.handle(str(pos[0]) +','+str(pos[1]))
        #draw

    def sendTouch(self, LED):
        LEDx, LEDy = LED
        if self.penDown:
            #checking distance between pen strokes -- don't want misfires to draw lines
            if self.lastPen is not None:
                if abs(self.lastPen[0] - LEDx) > 10 or abs(self.lastPen[1] - LEDy) > 10:
                    self.up()
                    self.down((LEDx, LEDy))
            self.newLEDPos((LEDx,LEDy))
        else:
            self.down((LEDx, LEDy))


    def borderCheck(self,img):
        #CHECKING FOR BORDER
        if self.debug:
            print('borderCheck')
        if self.border is None:
            self.border = Border(debug=self.debug)
            if self.prod:
                pass
        if self.corners < 4:
            img1 = cvHelper.colorSelect2(img.copy())
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

            print('corner')
            if self.corners ==0:
                #topLeft, NW
                print('nw')
                if not self.calibrating:
                    self.p.calibNW()
                    self.calibrating = True
                    self.framesToSkip = 5
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'topleft'):
                        print('found nw')
                        self.corners += 1
                        self.calibrating = False
                        self.framesToSkip = 5
                else:
                    self.framesToSkip -=1
            elif self.corners == 1:
                #topRight, NE
                print('ne')
                if not self.calibrating:
                    self.p.calibNE()
                    self.calibrating = True
                    self.framesToSkip = 5
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'topright'):
                        self.calibrating = False
                        print('found ne')
                        self.corners += 1
                        self.framesToSkip = 5
                else:
                    self.framesToSkip -=1
            elif self.corners == 2:
                #bottomleft, SW
                print('sw')
                if not self.calibrating:
                    self.p.calibSW()
                    self.calibrating = True
                    self.framesToSkip = 5
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'bottomleft'):
                        print('found sw')
                        self.calibrating = False
                        self.corners += 1
                else:
                    self.framesToSkip -=1
            elif self.corners == 3:
                #bottomright, SE
                print('se')
                if not self.calibrating:
                    self.p.calibSE()
                    self.calibrating = True
                    self.framesToSkip = 5
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'bottomright'):
                        print('found se')
                        self.calibrating = False
                        self.corners += 1
                        self.p.doneCalib()
                else:
                    self.framesToSkip -= 1
        else:
            if self.debug:
                print('not checking for border')
            return True

    def nextFrame(self, img):
        if self.debug:
            print("next Frame")
            cv2.waitKey(1)

        #checks if border exists.  If it hasn't continue to look for it
        if not self.borderCheck(img):
            return
            
        #SHOW BORDER
        if self.debug:
            box = np.int0(self.border.borderboundries)
            img2 = img.copy()
            img2 = cv2.drawContours(img2, [box], 0, (255,0,255) ,2)
        
        #CHECKING FOR LED
        img1 = cvHelper.colorSelect(img.copy())
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        LED = self.detectLED(img1)
        if LED is not None:
            LEDx, LEDy = self.border.getPositionOfPoint(LED)
            if self.debug:
                img2 = cv2.circle(img2, LED, 5, (0,255,0), 2)
                print((LEDx, LEDy))
            if self.prod:
                self.sendTouch((LEDx,LEDy))
        else:
            if self.debug:
                print('No LED')
            if self.prod:
                if self.penDown:
                    self.upcount +=1
                    if self.upcount > 15:
                        self.up()

        if self.debug:
            cv2.imshow('img2', img2)

    def detectLED(self, img):
        #cv modes and methods
        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        #contours from image
        _,contours,_ = cv2.findContours(img,modes[0], methods[1])
        #sorted by smalles perimeters first
        cv2.imshow('detectLED', img)
        contours = sorted(contours, key=lambda x: cv2.arcLength(x, True))
        print(len(contours)) 
    
        #cycle through contours to find LED
        for c in contours:
            #weed out contours that are too large or too small
            if cv2.arcLength(c, False) < 20 or cv2.arcLength(c, True) > 60:
                continue
            #smallest circle closing the contour
            (x,y),_ = cv2.minEnclosingCircle(c)
            x = int(x)
            y = int(y)
            #remove
            #return first in circle. 
            #TODO get more specific?
            if self.border.inBorder((x,y)):
                return (x,y)
        return None

    def recalibrate(self):
        self.border = None
        self.penDown = False
        self.lastPen = None
        self.calibrating = False
        self.corners = 0
    #this method reads images sent over a socket via the slave whiteboard.

    def runVideo(self):
        self.connect()
        if self.debug:
            print("runVideo")
        connection = self.s.makefile('rb')
        while True:
            try:
                #Socket first sends how long the image will be
                imLen = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                while not imLen:
                    if self.debug:
                        print("Waiting for imLen")
                    #assume network issues for no imLen
                    #TODO
                    imLen = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                if self.debug:
                    print('imLen: {}'.format(imLen))

                stream = io.BytesIO()
                stream.write(connection.read(imLen))
                #data is the image recieved from the stream converted for opencv
                data = np.fromstring(stream.getvalue(), dtype=np.uint8)
                img = cv2.imdecode(data,1)
                cv2.imshow('original', img)
                self.nextFrame(img) 
            except Exception as e:
                print("Socket Error: whiteboardView.whiteboardView.runVideo")
                print(e)
                
    #this is mostly for testing. can break video frame by frame
    #video can be given via file path, camera port(as int), or via url
    #ex. /path/to/file, 0, tcp//@ip:port
    def runVideoFromPath(self, videoPath):
        self.video = True
        if self.debug:
            print("runVideo({})".format(videoPath))
        cap = cv2.VideoCapture(videoPath)

        ret, img = cap.read()
        if not ret and self.debug:
            print("no video")
        while ret:
            self.nextFrame(img)
            if self.debug:
                cv2.waitKey(0)
            ret, img = cap.read()


    def close(self):
        self.s.close()
        cv2.DestroyAllWindows()
        
def main():
    from whiteboardView import cvHelper
    cv2.waitKey(0)
if __name__ == '__main__':
    main()
