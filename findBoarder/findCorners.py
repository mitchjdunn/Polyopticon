import numpy as np
import cv2 
import glob

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

#checkerboard size
checkerx=126
checkery=3

#prepare object points
objp=np.zeros((checkerx*checkery,3), np.float32)
objp[:,:2]=np.mgrid[0:checkerx,0:checkery].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

images = glob.glob('checkerboard1.png')

for fname in images:
	print(fname)
	img = cv2.imread(fname)
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	
	cv2.imshow('gray',gray)
	cv2.waitKey()
	cv2.destroyAllWindows()
	#find the chess board corners
	ret, corners = cv2.findChessboardCorners(gray, (checkerx, checkery), None)

	print(ret)
	if ret == True:
		print("found")
		objpoints.append(objp)
		
		corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
		imgpoints.append(corners2)

		# Draw and display the corners
		cv2.drawChessboardCorners(img, (7,6), corners2,ret)
		cv2.imshow('img',img)
		cv2.imwrite('checkers.jpg',img)
