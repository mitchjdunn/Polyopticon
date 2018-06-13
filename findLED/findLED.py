import cv2
import numpy as np
from matplotlib import pyplot as plt


def templateMatch(img, template, method):
	res = cv2.matchTemplate(img, template, method)
	min_val ,max_val, min_loc, max_loc = cv2.minMaxLoc(res)
	top_left = max_loc 
	bottom_right = (top_left[0] + w, top_left[1] + h)
	cv2.rectangle(img, top_left, bottom_right,255,2)
	return img

def detectCircle(img):
	circles = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT, 10, 200, param1=80, param2=50, minRadius=5, maxRadius=30)
	if circles is not None:
		circles = np.round(circles[0,:]).astype("int")
	else:
		return []
	return circles
	for circle in circles:
		return circle

def addEdges(img):
	edges = cv2.Canny(img,50,25)
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

def threshold(img):
	#eh, img = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
	img = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
	return img

def colorSelect(img):
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	lower_white = np.array([0,0,150])
	upper_white = np.array([20,20,255])
	mask = cv2.inRange(hsv, lower_white, upper_white)
	return cv2.bitwise_and(img,img, mask= mask)

#template and template size
#template = cv2.imread('/home/mitch/opencv_workspace/findLED/stills/ledwithedge.jpg',0)
#w, h = template.shape[::-1]

#single image
#img = cv2.imread('stills/fullboardwithled.jpg')
#x,y,r=detectCircle(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
#img = addEdges(img)

#img = cv2.circle(img, (x,y),r,(0,250,0),2)
#cv2.imshow('circle', img)
#cv2.waitKey(0)
#video
cap = cv2.VideoCapture('/home/mitch/opencv_workspace/findLED/projtest5.h264')

ret, img = cap.read()
cv2.waitKey(50)
while ret:
	#shows imaged with matching template
	img2 = colorSelect(img)
	circles = detectCircle(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY))
	for x,y,r in circles:
		img = cv2.circle(img, (x,y),r,(0,250,0),2)

	
	cv2.imshow('video',img)
	cv2.waitKey(10)
	ret, img = cap.read()


#cap.release()
cv2.destroyAllWindows()


