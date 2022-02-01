# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
import statistics

#function for getting initial ball coordinates from mouse
def get_ball(event,x,y,flags,param):
	if event == cv2.EVENT_LBUTTONDBLCLK:
		global init_x, init_y
		init_x = x
		init_y = y

#crops frame, taking into account the borders of the image
def cropframe(frame, n):
	if init_x-n < 0:
		x1 = 0
		x2 = 2*n
	else:
		x1 = init_x-n
		x2 = init_x+n
	if init_y-n < 0:
		y1 = 0
		y2 = 2*n
	else:
		y1 = init_y-n
		y2 = init_y+n
	return frame[y1:y2, x1:x2]

#adjust frame center according to the last known position of ball
def adjustcenter(M, n):
	global init_x, init_y
	print(init_x, init_y)
	if init_x-n < 0:
		init_x = init_x + int(M["m10"] / M["m00"])
	else:
		init_x = init_x + int(M["m10"] / M["m00"]) - n
	if init_y-n < 0:
		init_y = init_y + int(M["m01"] / M["m00"])
	else:
		init_y = init_y + int(M["m01"] / M["m00"]) - n

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
	help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64,
	help="max buffer size")
args = vars(ap.parse_args())

# define the lower and upper boundaries of the color of the
# ball in the HSV color space, then initialize the
# list of tracked points
greenLower = (20, 80, 86)
greenUpper = (32, 200, 255)

# this list of tracked points will be used to calculate vector of ball
#it will have a max length
pts = deque(maxlen=args["buffer"])
# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
	vs = VideoStream(src=0).start()
# otherwise, grab a reference to the video file
else:
	vs = cv2.VideoCapture(args["video"])
# allow the camera or video file to warm up
time.sleep(0.5)

#display initial frame for clicking on ball position
frame = vs.read()
frame = frame[1] if args.get("video", False) else frame
frame = imutils.resize(frame, width=1000)
cv2.imshow('initial frame', frame)
cv2.moveWindow('initial frame', 40,30)
cv2.setMouseCallback('initial frame', get_ball)
#press enter after doubleclicking
cv2.waitKey()

# This is the loop for video processing
while True:
	# grab the current frame
	frame = vs.read()
	# handle the frame from VideoCapture or VideoStream
	frame = frame[1] if args.get("video", False) else frame
	# if we are viewing a video and we did not grab a frame,
	# then we have reached the end of the video
	if frame is None:
		break
	# resize the frame
	frame = imutils.resize(frame, width=1000)
	#define cropped frame dimensions
	#crop frame, make sure edges aren't out of bounds
	n = 80
	#crop frame, make sure edges aren't out of bounds
	cropped = cropframe(frame,n)
	#blur frame
	blur = cv2.GaussianBlur(cropped, (11, 11), 0)
	# change frame to hsv color space
	hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
	# construct a mask by eliminating all colors except for the color "green",
	mask = cv2.inRange(hsv, greenLower, greenUpper)

	# perform a series of dilations and erosions to remove any small
	# blobs left in the mask
	# mask = cv2.erode(mask, None, iterations=1)
	# mask = cv2.dilate(mask, None, iterations=1)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	center = None
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		arealist = []
		pointlist = []
		for i in cnts:
			area = cv2.contourArea(i)
			if area >= 0 and area <= 200:
				pointlist.append(i)
				arealist.append(area)

		index = int(len(arealist)*.75 )
		points = pointlist[index]

	if len(cnts) > 0:
		c = points


		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Occupied"

		#m00 will be zero if contour isn't a closed shape
		if M["m00"] > 0:
			#change frame center to center of this contour
			adjustcenter(M, n)
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x), int(y)), int(radius),
				(0, 255, 255), 25)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
	# update the points queue
	if center != None:
		pts.appendleft(center)

	# display frames in windows
	cv2.imshow("frame", frame)
	cv2.moveWindow("frame", 40,30)
	cv2.imshow("mask", mask)
	cv2.moveWindow("mask", 1000,30)
	cv2.imshow("cropped", cropped)
	cv2.moveWindow("cropped", 40,700)
	key = cv2.waitKey(1) & 0xFF
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

	time.sleep(0.1)
# if we are not using a video file, stop the camera video stream
if not args.get("video", False):
	vs.stop()
# otherwise, release the camera
else:
	vs.release()
# close all windows
cv2.destroyAllWindows()
