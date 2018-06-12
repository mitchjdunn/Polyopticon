import cv2
import numpy as np
from matplotlib import pyplot as plt

template = cv2.imread('stills/irled.jpg',0)
cap = cv2.VideoCapture('projtest1.h264')
w, h = template.shape[::-1]

method = cv2.TM_CCEOFF
# All the 6 methods for comparison in a list
#methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
#			'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']

n=1
while(cap.isOpened()):
	ret, img = cap.read()
	res = cv2.matchTemplate(img,template,method)
	min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
	top_left = max_loc
	bottom_right = (top_left[0] + w, top_left[1] + h)

	cv2.rectangle(img,top_left, bottom_right, 255, 2)

	plt.subplot(121),plt.imshow(res,cmap = 'gray')
	plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
	plt.subplot(122),plt.imshow(img,cmap = 'gray')
	plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
	plt.suptitle(meth)
	cv2.imwrite('videoStills/'+str(n).nzfill(10)+'.jpg', img)
