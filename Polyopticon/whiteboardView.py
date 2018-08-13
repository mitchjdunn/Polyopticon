from time import sleep #used to pause thread 
import cv2 # OpenCV python library
import socket # used for remote process communication
import numpy as np # Helps manipulate data given from openCV
import math
import io 
import struct
from border import Border

class cvHelper:

    #color select white
    # param img is the image to be maniuplated
    # returns the image with everything but a specific range of white filtered out
    def colorSelect(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_white = np.array([0,0,245])
         upper_white = np.array([180,15,255])
         mask = cv2.inRange(hsv, lower_white, upper_white)
         return cv2.bitwise_and(img,img, mask= mask)

    #color select blue
    # param img is the image to be maniuplated
    # returns the image with everything but a specific range of blues filtered out
    def colorSelect2(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_blue = np.array([80,60,125])
         upper_blue = np.array([130,255,255])
         mask = cv2.inRange(hsv, lower_blue, upper_blue)
         # cv2.imshow('colorSelect2', cv2.bitwise_and(img,img, mask= mask))
         return cv2.bitwise_and(img,img, mask= mask)

#This class is created and managed by the master whiteboard
#It should only be called when a slave whiteboard with a camera is created
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
        self.framesToSkip = 10
        self.corners = 0
        self.video = False
        self.ports = [4545,4546,4547,4548]
        self.s = socket.socket()
        self.videoName = None
        self.videoWriter = None
        #Socket for video stream
        self.videosocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # opens socket to camera that is streaming video
    def connect(self):
        sleep(2)
        # multiple ports incase one is taken
        for port in self.ports:
            try:
                if self.debug:
                    print((self.p.slaveIP, port)) 
                self.s.connect((self.p.slaveIP, port))
                return
            except:
                print('port {} failed'.format(port))
                pass
    
    # sends up message to master whiteboard
    def up(self):
        self.penDown = False
        self.p.handle('up') 
        self.upcount=0

    #sends down message to master whiteboard
    # param pos is the position of the LED
    def down(self, pos):
        self.upcount=0
        self.penDown = True
        self.p.handle("down," + str(pos[0]) + ',' + str(pos[1]))

    # sends LED position to master whiteboardd
    # param pos is the position of the LED
    def newLEDPos(self, pos):
        self.lastPen = pos
        self.p.handle(str(pos[0]) +','+str(pos[1]))
        #draw

    # Some logic to determine what message gets sent to master whiteboard
    # param LED is the coordinates of the touch
    def sendTouch(self, LED):
        LEDx, LEDy = LED
        if self.penDown:
            #checking distance between pen strokes -- don't want misfires to draw lines
            if self.lastPen is not None:
                # if lest pen stroke is more than 10 pixels away send up then down to stop lines from being drawn
                if abs(self.lastPen[0] - LEDx) > 10 or abs(self.lastPen[1] - LEDy) > 10:
                    self.up()
                    self.down((LEDx, LEDy))
            self.newLEDPos((LEDx,LEDy))
        else:
            self.down((LEDx, LEDy))

    # checks if border is found.  Tries to find it if it is not.
    # param img is the image to check for boarder
    # returns true if border is found, false otherwise
    def borderCheck(self,img):
        #CHECKING FOR BORDER
        if self.debug:
            print('borderCheck')
        if self.border is None:
            self.border = Border(debug=self.debug)
            if self.prod:
                pass
        # preps the image recieved to find the corners
        if self.corners < 4:
            img1 = cvHelper.colorSelect2(img.copy())
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

            # Tells the master whiteboard to display the top left corner
            if self.corners ==0:
                #topLeft, NW
                print('nw')
                if not self.calibrating:
                    self.p.calibNW()
                    self.calibrating = True
                    self.framesToSkip = 10
                # wait a couple of frames to make sure we are detecting the calibration screen
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'topleft'):
                        print('found nw')
                        self.corners += 1
                        self.calibrating = False
                        self.framesToSkip = 10
                else:
                    self.framesToSkip -=1
            # Tells the master whiteboard to display the top right corner
            elif self.corners == 1:
                #topRight, NE
                print('ne')
                if not self.calibrating:
                    self.p.calibNE()
                    self.calibrating = True
                    self.framesToSkip = 10
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'topright'):
                        self.calibrating = False
                        print('found ne')
                        self.corners += 1
                        self.framesToSkip = 10
                else:
                    self.framesToSkip -=1
            # Tells the master whiteboard to display the bottom left corner
            elif self.corners == 2:
                #bottomleft, SW
                print('sw')
                if not self.calibrating:
                    self.p.calibSW()
                    self.calibrating = True
                    self.framesToSkip = 5
                # wait a couple of frames to make sure we are detecting the calibration screen
                if self.framesToSkip == 0:
                    if self.border.findCorner(img1, 'bottomleft'):
                        print('found sw')
                        self.calibrating = False
                        self.corners += 1
                else:
                    self.framesToSkip -=1
            # Tells the master whiteboard to display the bottom right corner
            elif self.corners == 3:
                #bottomright, SE
                print('se')
                if not self.calibrating:
                    self.p.calibSE()
                    self.calibrating = True
                    self.framesToSkip = 5
                # wait a couple of frames to make sure we are detecting the calibration screen
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

    # Step through the video frame by frame.  Holds the logic of the image recognition
    # param img is the current frame from the video
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
                    self.up()

        if self.debug:
            cv2.imshow('img2', img2)

    # Detects the LED by grabbing all the white and finding the clusters of colored pixels.
    # param img is the binary (greyscaled) image to find the LED
    # returns the coordinates of the detected LED1
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
            if cv2.arcLength(c, False) < 15 or cv2.arcLength(c, True) > 60:
                continue
            #smallest circle closing the contour
            (x,y),_ = cv2.minEnclosingCircle(c)
            x = int(x)
            y = int(y)
            #return first in circle. 
            #TODO get more specific?
            if self.border.inBorder((x,y)):
                return (x,y)
        return None

    # this method sets everything up to be recalibrated.
    # called by the master whiteboard
    def recalibrate(self):
        self.border = None
        self.penDown = False
        self.lastPen = None
        self.calibrating = False
        self.corners = 0
    # this method sets the file path to save the video
    # called by the master whiteboard
    # param filePath is the filepath to save the video
    def save(self, filePath):
        self.videoName = filePath
        print(filePath)
        sleep(2)

    # this method reads images sent over a socket via the slave whiteboard and calls nextFrame for every frame
    def runVideo(self):
        self.connect()
        if self.debug:
            print("runVideo")
        connection = self.s.makefile('rb')
        fourcc = cv2.VideoWriter_fourcc(*'XVID') 
        # how to save the video ##### NO SOUND
        self.videoWriter = cv2.VideoWriter('whiteboardVideo.avi', fourcc, 15, (1280,720))
        while True:
            try:
                #Socket first sends how long the image will be
                imLen = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                while not imLen:
                    if self.debug:
                        print("Waiting for imLen")
                    #assume network issues for no imLen
                    imLen = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                if self.debug:
                    print('imLen: {}'.format(imLen))

                stream = io.BytesIO()
                stream.write(connection.read(imLen))
                #data is the image recieved from the stream converted for opencv
                data = np.fromstring(stream.getvalue(), dtype=np.uint8)
                img = cv2.imdecode(data,1)
                cv2.imshow('original', img)
                self.videoWriter.write(img)
                print('writing video')
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


    # called by Master whiteboard to close all sockets and save/delete video found
    def close(self):
        self.videoWriter.release()
        if self.debug:
            print('whiteboardView.close')
        self.s.close()
        if self.videoName is None:
            os.remove('whiteboardVideo.avi')    
            pass
        else:
            os.rename('whiteboardVideo.avi', self.videoName)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
def main():
    from whiteboardView import cvHelper
    cv2.waitKey(0)
if __name__ == '__main__':
    main()
