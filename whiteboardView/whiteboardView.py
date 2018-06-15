import cv2
import math
import numpy as np
from matplotlib import pyplot as plt

class whiteboardView:

	def __init__(self_):
		print(starting)
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

	def detectRectangle(img):
		lines = cv2.HoughLinesP(img, 1, math.pi/2, 100, minLineLength=300)
		if lines is not None:
			return lines[:,0,:]#[:4]
		return []
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

	def adaptiveThreshold(img):
		#eh, img = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
		img = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,5)
		cv2.imshow('threshold', img)
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
		img2 = whiteboardView.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
		cv2.imshow('img2',img2)
		#img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		rectangles = whiteboardView.detectRectangle(img2)
				
		for x1,y1,x2,y2 in rectangles:
			img = cv2.line(img,(x1,y1),(x2,y2),(255,0,0),2)
		cv2.imshow('line', img)
		cv2.waitKey()

	def findOrigin(img):
		img = whiteboardView.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
		#img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		rectangles = whiteboardView.detectRectangle(img)
		return(min(rectangles[:,0]),min(rectangles[:,1]))

	def findBoarderByTemplate(img, template):
		w,h = template.shape[::-1]
		res = cv2.matchTemplate(img, template, cv2.TM_COEEF)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		top_left = max_loc
		bottom_right = (top_left[0] + w, top_left[1] + h)
		cv2.rectangle(img,top_left,bottom_right,(255,0,0),2)
		cv2.imshow('frame', img)
		
	def trackLED(cap):
		ret, img = cap.read()
		cv2.waitKey(50)
		while ret:
			img2 = whiteboardView.colorSelect(img)
			circles = whiteboardView.detectCircle(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY))
			for x,y,r in circles:
				img = cv2.circle(img, (x,y),r,(0,250,0),2)
		
			
			cv2.imshow('video',img)
			cv2.waitKey(10)
			ret, img = cap.read()
		cap.release()
		cv2.destroyAllWindows()
		

	#cap.release()			
	##single image
	#img = cv2.imread('rectangleboard.png')
	#img2 = colorSelect(img)
	#circles = detectCircle(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY))
	#for x,y,r in circles:
	#	img = cv2.circle(img, (x,y),r,(0,250,0),2)
	#rectangles = detectRectangle(img2)
	#print(rectangles)
	#for x1,y1,x2,y2 in rectangles:
	##TODO don't add lines to image -- just need the smalles x and the smallest y as origin
	#	img = cv2.line(img,(x1,y1),(x2,y2),(255,0,0),2)
	#	cv2.imshow('line', img)
	#	cv2.waitKey()
	#cv2.imshow('rect', img)
	#cv2.waitKey()
	#video
	#cap = cv2.VideoCapture('/home/mitch/opencv_workspace/findLED/projtest1.h264')
	#
	
#whiteboardView.trackLED(cv2.VideoCapture('tests/vids/projtest6.h264'))
#whiteboardView.findOrigin(cv2.imread('tests/stills/rectangleboard.png'))
whiteboardView.findBoarderByTemplate(whiteboardView.threshold(cv2.cvtColor(cv2.imread('test4.jpg'),cv2.COLOR_BGR2GRAY)), cv2.imread('templateBorder.jpg'))
cv2.waitKey()
cv2.destroyAllWindows()
