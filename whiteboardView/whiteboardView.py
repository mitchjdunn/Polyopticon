import socket
import cv2
import numpy as np
import math
class whiteboardView():

    self.rectangle = ((838,159),(1716,659))
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
        point1=(838, 159)
        point2=(1716,659)
        cap = cv2.VideoCapture(video)
        out = cv2.VideoWriter('lights.mp4', cv2.VideoWriter_fourcc('F','M','P','4'), 30.0, (1920,1080))
        ret, img = cap.read()
        counter = -1
        sock = whiteboardView.connect("192.168.1.79", 15273)
        while ret:
            cv2.waitKey(10)
            r1,r2=whiteboardView.templateMatch(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.cvtColor(template, cv2.COLOR_BGR2GRAY))
            if r1[0] > 880  and r1[1] > 169 and r2[0] < 1710 and r2[1] < 630:
            #if r1[0] > point1[0]  and r1[1] > point1[1] and r2[0] < point2[0] and r2[1] < point2[1]:
                mesg = ""
                if counter==-1:
                    mesg+="down,"
                    counter = 0
                img = cv2.rectangle(img, r1,r2,(0,250,0),2)
                x,y = whiteboardView.getPositionAsPercent((r1[0] - point1[0], r1[1] - point1[1]),(point2[0] - point1[0],point2[1]-point1[1]))
                mesg +=str(x) +"," + str(y) + "\n"
                whiteboardView.send(mesg,sock)
                #send coordinates to whiteboard
            else:
                if counter == 5:
                    whiteboardView.send("up\n", sock)
                    counter = -1
                elif counter != -1:
                    counter = counter +1
            out.write(img)
            cv2.imshow('fuckyoujon', img)           
            ret, img = cap.read()
            
        cap.release()
        out.release() 
