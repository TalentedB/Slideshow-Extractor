# importing libraries
import cv2
import numpy as np
from fpdf import FPDF
from time import sleep
import os
from pytube import YouTube
import argparse

def Download(link: str):
    youtubeObject = YouTube(link)
    youtubeObject = youtubeObject.streams.get_highest_resolution()
    try:
        youtubeObject.download("temp", filename="tempvideo.mp4")
    except:
        print("An error has occurred downloading the video")
        exit(0)
    print("Downloaded video successfully")



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
	# Return the percentage changed between frames
	return percentage_changed


def ExtractSlidesToPDF(video_path: str = 'thevideo.mp4', output_path: str = 'slides.pdf', threshold: int = 2):
	
	threshold = threshold or 2
	video_path = video_path or 'thevideo.mp4'
	output_path = output_path or 'slides.pdf'


	# Create a VideoCapture object and read from input file
	print("Extracting Slides...")
	cap = cv2.VideoCapture(video_path)
	pdf = FPDF()
	image_list = []

	# Check if camera opened successfully
	if (cap.isOpened()== False):
		print("Error opening video file")
		exit(1)


	# Get first frame
	ret, frame = cap.read()
	prev_frame = frame
	cv2.imwrite(f'temp/temp{len(image_list)}.png', cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))
	image_list.append(f'temp/temp{len(image_list)}.png')


	# Read until video is completed
	
	counter = 0
	while(cap.isOpened()):
		counter += 1
		# Capture frame-by-frame
		ret, frame = cap.read()
		if ret == True:
			if compare_frames(frame, prev_frame) > threshold:
				cv2.imwrite(f'temp/temp{len(image_list)}.png', cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))
				image_list.append(f'temp/temp{len(image_list)}.png')
			prev_frame = frame		
	# Break the loop if done reading
		else:
			break

	# Combine all images into a PDF
	for image in image_list:
		pdf.add_page()
		pdf.image(image, 0, 0, 210, 297)
		os.remove(image)

	pdf.output(output_path, "F")
	#Release the camera port
	cap.release()

	# Closes all the frames
	cv2.destroyAllWindows()

def initProgram():
	# User Chooses Options:
	print("Welcome to the Slide Extractor!")
	print("Please choose an option:")
	print("1. Extract Slides from Video (Local)")
	print("2. Extract video from youtube link")
	print("3. Exit")
	choice = input("Enter your choice: ")
	if choice == "1":
		threshold = input("Enter the threshold (default is 2): ")
		video_path = input("Enter the video path: ")
		ExtractSlidesToPDF(threshold=threshold, video_path=video_path)
		print("Exported Slides Successfully")
		exit(0)
	if choice == "2":
		threshold = input("Enter the threshold (default is 2): ")
		video_path = input("Enter the video link (youtube): ")
		Download(link=video_path)
		ExtractSlidesToPDF(threshold=threshold, video_path="temp/tempvideo.mp4")
		os.remove("temp/tempvideo.mp4")
		print("Exported Slides Successfully")
		exit(0)
	if choice == "3":
		print("Exiting...")
		exit(0)
	else:
		print("Invalid choice, please try again")
		initProgram()
	




def main():
	parser = argparse.ArgumentParser(description='Video Extraction Script')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--youtube', '-y', metavar='<video_url>', help='URL of the YouTube video')
	group.add_argument('--file', '-f', metavar='<video_path>', help='Path to the video file')
	parser.add_argument('--threshold', '-t', metavar='<value>', type=float, help='Threshold value for slide change detection')
	parser.add_argument('--output', '-o', metavar='<output_path>', help='Path to the output file')

	args = parser.parse_args()

	if args.youtube:	
		# Process YouTube video URL
		Download(link=args.youtube)
		ExtractSlidesToPDF(threshold=args.threshold, video_path="temp/tempvideo.mp4", output_path=args.output)
		os.remove("temp/tempvideo.mp4")

	elif args.file:
		# Process Video file path
		ExtractSlidesToPDF(threshold=args.threshold, video_path=args.file, output_path=args.output)
	else:
		# ? Invalid arguments passed and or missing arguemnts
		print('Invalid arguments')
		exit(1)

		



if __name__ == '__main__':
	main()


