# importing libraries
import cv2
import numpy as np
from fpdf import FPDF
from time import sleep
import os





def compare_frames(frame1, frame2):
	# Convert frames to grayscale for comparison
	gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
	gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

	# Compute the absolute difference between the frames
	frame_diff = cv2.absdiff(gray1, gray2)

	# Apply thresholding to emphasize the differences
	_, threshold = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
	total_pixels = threshold.size
	changed_pixels = np.count_nonzero(threshold)
	percentage_changed = (changed_pixels / total_pixels) * 100
	# print(percentage_changed)
	return percentage_changed


def ExtractSlidesToPDF(video_path: str = 'thevideo.mp4', output_path: str = 'slides.pdf'):
	# Create a VideoCapture object and read from input file
	cap = cv2.VideoCapture(video_path)
	pdf = FPDF()

	# Check if camera opened successfully
	if (cap.isOpened()== False):
		print("Error opening video file")


	# Get first frame
	ret, frame = cap.read()
	prev_frame = frame



	# Read until video is completed
	image_list = []
	counter = 0
	while(cap.isOpened()):
		counter += 1
		# Capture frame-by-frame
		ret, frame = cap.read()
		if ret == True:
			if compare_frames(frame, prev_frame) > 2:
				cv2.imwrite(f'temp/temp{len(image_list)}.png', cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))
				image_list.append(f'temp/temp{len(image_list)}.png')
			prev_frame = frame
				
	# Break the loop
		else:
			break


	for image in image_list:
		pdf.add_page()
		pdf.image(image, 0, 0, 210, 297)
		os.remove(image)

	pdf.output(output_path, "F")
	#Release the camera port
	cap.release()

	# Closes all the frames
	cap.release()
	cv2.destroyAllWindows()

ExtractSlidesToPDF()




