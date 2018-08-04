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

    def colorSelect2(img):
         hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
         lower_white = np.array([0,0,200])
         upper_white = np.array([240,80,255])
         mask = cv2.inRange(hsv, lower_white, upper_white)
         return cv2.bitwise_and(img,img, mask= mask)

class WhiteboardView:


    def __init__(self, whiteboard, debug=False, prod=False):
        self.p = whiteboard
        self.border = None
        self.debug = debug
        self.prod = prod
        self.penDown = False
        self.lastPen = None
        self.readyMessageSent = False
        self.s = socket.socket()
        self.ports = [4545,4546,4547,4548]


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
            cv2.imshow('original Image', img)
            cv2.waitKey(1)
        #CHECKING FOR BORDER
        if self.border is None:
            self.border = Border()
            if self.prod:
                pass
                #TODO handle calibration
                #self.send('calibrating')
        if not self.border.borderFound:
            #CHANGE IMG BEFORE FINDBORDER
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
        #img1 = WhiteboardView.colorSelect(img.copy())
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
                self.nextFrame(img) 
            except:
                print('Error while recieving images via socket')        
                
    #this is mostly for testing. can break video frame by frame
    #video can be given via file path, camera port(as int), or via url
    #ex. /path/to/file, 0, tcp//@ip:port
    def runVideoFromPath(self, videoPath):
        if self.debug:
            print("runVideo({})".format(videoPath))
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
    p = Paint(master = True, debug=True)
    #Get host from network discovery.
    while not p.slaveAttached:
        print("slave not found")
        sleep(1)
    try:
        w = WhiteboardView(p, debug=True, prod=True)
        #w.connect()
        #threading.Thread(target=w.runVideo).start() 
    except:
        print("is kill")
    
    p.startLoop()
    #w.runVideo("udp://@" + host + ":" + port)

if __name__ == '__main__':
    main()
