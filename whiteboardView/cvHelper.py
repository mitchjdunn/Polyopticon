import cv2
import math
import numpy as np
import socket
class cvHelper:

    def __init__(self_):
        print(starting)

    def templateMatch(img, template):
        method = cv2.TM_CCOEFF
        res = cv2.matchTemplate(img, template, method)
        w = template.shape[1]
        h = template.shape[0]
        min_val ,max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc 
        bottom_right = (top_left[0] + w, top_left[1] + h)
        return(top_left, bottom_right)
       
    def templateMatch2(img,template):
        #template = cvHelper.colorSelect(template)
        #img2= cvHelper.colorSelect(img)
        r1,r2 = cvHelper.templateMatch(img2, template)
        return cv2.rectangle(img,r1,r2, (0,0,255),2)

    def detectCircle(img):
        circles = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT, 10, 100, param1=100, param2=50,  maxRadius=15)
        if circles is not None:
            circles = np.round(circles[0,:]).astype("int")
        else:
            return []
        return circles

    def detectRectangle(img):
        lines = cv2.HoughLinesP(img, 1, math.pi/2, 100, minLineLength=300)
        if lines is not None:
            return lines[:,0,:]#[:4]
        return []
    def addEdges(img):
        edges = cv2.Canny(img,80,40)
        return edges
        img = cv2.addWeighted(img, .7, edges, .3,0)
        return img

    def brighten(img, value):
        hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        hsv[:,:,2]+=value
        img=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
        return img

    def darken(img, value):
        hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        hsv[:,:,2]-=value
        img=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
        return img


    def adaptiveThreshold(img):
        #eh, img = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,5)
        return img

    def threshold(img):
        ret, img = cv2.threshold(img,200,225,cv2.THRESH_BINARY)
        cv2.imshow('img', img)
        cv2.waitKey()
        return img
    

    def colorSelect(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0,0,150])
        upper_white = np.array([20,20,255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        return cv2.bitwise_and(img,img, mask= mask)

    def colorSelect2(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0,0,200])
        upper_white = np.array([240,80,255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        return cv2.bitwise_and(img,img, mask= mask)

    #template and template size
    #template = cv2.imread('/home/mitch/opencv_workspace/findLED/stills/ledwithedge.jpg',0)
    #w, h = template.shape[::-1]

    def showRectangle(img):
        img2 = cvHelper.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        cv2.imshow('img2',img2)
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rectangles = cvHelper.detectRectangle(img2)
                
        for x1,y1,x2,y2 in rectangles:
            img = cv2.line(img,(x1,y1),(x2,y2),(255,0,0),2)
        cv2.imshow('line', img)
        cv2.waitKey()

    def findOrigin(img):
        img = cvHelper.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rectangles = cvHelper.detectRectangle(img)
        return(min(rectangles[:,0]),min(rectangles[:,1]))

    def findBorderByTemplate(img, template):
        img = cvHelper.colorSelect2(img)
        return cvHelper.templateMatch2(img, template)
    def rotatedRectangle(img):
        img2 = cvHelper.colorSelect2(img)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        #img2 = (255-img2)
        modes=[cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE, cv2.RETR_FLOODFILL]
        methods=[cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE]
        _,contours,_ = cv2.findContours(img2,modes[3], methods[0])
        print(contours)
        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        print("this is box")
        print([box])
        cv2.imshow('img2',img2)
        return cv2.drawContours(img, [box], 0,(0,0,255),2)
    #goes frame by frame and shows how function effects the video
    #function must take an unedited image as the only parameter.
    #and return the edited image
    def showEditedVideo(filename, function, args= None):
        
        cap = cv2.VideoCapture(filename)
        ret, img = cap.read()
        cv2.waitKey(50)
        while ret:
            cv2.imshow('uneditedVideo',img)
            if args is None:
                img = function(img)
            else:
                img = function(img, *args)
            cv2.imshow('editedVideo',img)
            cv2.waitKey()
            ret, img = cap.read()
            
    def detectLED(img):
        img2 = cvHelper.colorSelect(img)
        circles = cvHelper.detectCircle(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY))
        for x,y,r in circles:
            img = cv2.circle(img2, (x,y),r,(0,250,0),2)
        
        return img
        
    def trackLED():
        major_ver, minor_ver, subminor_ver = str(cv2.__version__).split('.')
        print(cv2.__version__)
        tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN']
        tracker_type = tracker_types[3]
     
        template = cvHelper.colorSelect(cv2.imread('LEDTemplate.png'))
        if int(minor_ver) < 3:
            tracker = cv2.Tracker_create(tracker_type)
        else:
            if tracker_type == 'BOOSTING':
                tracker = cv2.TrackerBoosting_create()
            if tracker_type == 'MIL':
                tracker = cv2.TrackerMIL_create()
            if tracker_type == 'KCF':
                tracker = cv2.TrackerKCF_create()
            if tracker_type == 'TLD':
                tracker = cv2.TrackerTLD_create()
            if tracker_type == 'MEDIANFLOW':
                tracker = cv2.TrackerMedianFlow_create()
            if tracker_type == 'GOTURN':
                tracker = cv2.TrackerGOTURN_create()
        cap = cv2.VideoCapture('tests/vid/demotest-20s-30f-2-full.h264')
        LED=False
        ok, img = cap.read()
        cv2.waitKey(50)

      
        while ok:
            img2 = cvHelper.colorSelect(img)
            if not LED:
                box = cvHelper.templateMatch(img2, template)
                print('no LED')
                #in border
                if box[0][0] > 500 and box[1][0] < 1630 and box[0][1] > 25 and box[1][1] < 680:
                    print('found LED')
                    print(box)
                    tracker.init(img2, (box[0][0],box[0][1],box[1][0],box[1][1]))
                    LED = True
            
            LED, box = tracker.update(img2)
            
            if box[2] - box[0] < 15 or box[3] - box[1] < 15 or box[2] - box[0] > 50 or box[3] - box[1] > 50:
                print('resetting box')
                box = (0,0,0,0)
                #LED = False
            print(box)
            img2 = cv2.rectangle(img2, (int(box[0]),int(box[1])),(int(box[2]),int(box[3])),(0,0,255), 2)
            
            cv2.imshow('tracking', img2)
            ok, img = cap.read()
            cv2.waitKey()
    def templateCircles(img, template):
        img2 = cvHelper.colorSelect(img)
        circles = cvHelper.detectCircle(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY))
        box = cvHelper.templateMatch(img2, template)
        for x,y,r in circles:
            img = cv2.circle(img, (x,y),r,(0,250,0),2)
        img = cv2.rectangle(img, box[0],box[1], (0,0,255), 2)
        return img
 

#cvHelper.detectLED('tests/piTests/vid/demotest-20s--41-full.mp4', cv2.imread('LEDTemplate.png'))
#cvHelper.trackLED()
#cvHelper.showEditedVideo('tests/piTests/vid/demotest-20s--41-full.mp4', cvHelper.colorSelect)
print("hello")
cvHelper.showEditedVideo('tests/vids/projtest7.mp4', cvHelper.rotatedRectangle)
#cvHelper.showEditedVideo('tests/vid/demotest-20s-30f-2-full.h264', cvHelper.colorSelect2)
cv2.waitKey()
cv2.destroyAllWindows()
