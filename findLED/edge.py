import numpy as np
import cv2

img = cv2.imread('stills/fullboardwithled.jpg')
one = 80
two = 90
edges = cv2.Canny(img, one,two)
edges2 = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
dst = cv2.addWeighted(img, .7, edges2, .3,0)
cv2.imwrite('addWeighted.jpg', dst)
cv2.waitKey(0)
#
#while(one <= 100 and two <= 100):
#	edges = cv2.Canny(img, one,two)
#
#	cv2.imshow(str(one)+str(two), edges)
#	cv2.waitKey(0)
#	cv2.destroyAllWindows()
#	if two < 100:
#		two = two + 10
#	elif one < 100:
#		one = one + 10
#		two = 10
#	else:
#		break
