# importing libraries
import cv2
import numpy as np
from fpdf import FPDF
from time import sleep
import os
from pytube import YouTube
import argparse
import concurrent.futures

def Download(link: str):
    """Downloads a YouTube video from the given link to a temporary file.

    Args:
        link (str): The URL of the YouTube video.
    """
    youtubeObject = YouTube(link)
    youtubeObject = youtubeObject.streams.get_highest_resolution()
    try:
        youtubeObject.download("temp", filename="tempvideo.mp4")
    except Exception as e:
        print(f"An error has occurred downloading the video: {e}")
        print("Please check the YouTube link and your internet connection.")
        exit(1) # Exit with a non-zero status code to indicate failure
    print("Downloaded video successfully")



def compare_frames(frame1, frame2):
	"""Compares two video frames and returns the percentage of changed pixels.

	Args:
		frame1: The first frame (NumPy array).
		frame2: The second frame (NumPy array).

	Returns:
		float: The percentage of pixels that changed between the two frames.
	"""
	gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

	height, width = frame1.shape[:2]
	frame2_resized = cv2.resize(frame2, (width, height))
	gray2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2GRAY)

	frame_diff = cv2.absdiff(gray1, gray2)

	_, threshold_diff = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
	total_pixels = threshold_diff.size
	changed_pixels = np.count_nonzero(threshold_diff)
	percentage_changed = (changed_pixels / total_pixels) * 100
	return percentage_changed


def find_and_crop_slide(frame):
    """Identifies the largest contour in a frame, assumed to be a slide, and crops to it.

    Args:
        frame: The input video frame (NumPy array).

    Returns:
        NumPy array: The cropped frame, or the original frame if no contours are found
                     or if the crop is too small (though size check is not currently implemented here).
    """
    original_frame = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return original_frame # Return original if no contours found

    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    cropped_frame = original_frame[y:y+h, x:x+w]
    
    # Optional: If you want to ensure the cropped part is significant,
    # add a check here, e.g., if w*h is too small compared to frame size,
    # return original_frame. For now, we'll assume the largest contour is correct.

    return cropped_frame

def is_valid_slide_candidate(cropped_image, original_frame_shape, min_area_ratio=0.25, 
                             valid_aspect_ratios=None, aspect_ratio_tolerance=0.2):
    """Checks if a cropped image is a plausible slide/screen candidate.

    The validation is based on the cropped image's area relative to the original frame
    and its aspect ratio compared against a list of common screen/slide aspect ratios.

    Args:
        cropped_image (NumPy array): The image crop to validate.
        original_frame_shape (tuple): The shape (height, width) of the original video frame.
        min_area_ratio (float, optional): Minimum ratio of cropped_area / original_area 
                                        for the crop to be considered valid. Defaults to 0.25.
        valid_aspect_ratios (list, optional): A list of floats representing valid aspect 
                                            ratios (width/height). Defaults to [4/3, 16/9, 16/10].
        aspect_ratio_tolerance (float, optional): Percentage tolerance for matching aspect ratios. 
                                                Defaults to 0.2.

    Returns:
        tuple: (is_valid_bool, actual_area_ratio_float, actual_aspect_ratio_float)
               is_valid_bool is True if the candidate is valid.
               actual_area_ratio_float is the calculated area ratio.
               actual_aspect_ratio_float is the calculated aspect ratio of the crop.
    """
    if valid_aspect_ratios is None:
        valid_aspect_ratios = [(4/3), (16/9), (16/10)]

    cropped_h, cropped_w = cropped_image.shape[:2]
    original_h, original_w = original_frame_shape[:2]

    if cropped_h == 0 or cropped_w == 0 or original_h == 0 or original_w == 0:
        return False, 0.0, 0.0

    cropped_area = cropped_w * cropped_h
    original_area = original_w * original_h
    actual_area_ratio = cropped_area / original_area

    if actual_area_ratio < min_area_ratio:
        return False, actual_area_ratio, 0.0 # Crop is too small

    actual_aspect_ratio = cropped_w / cropped_h
    is_valid_aspect = False
    for target_ar in valid_aspect_ratios:
        if abs(actual_aspect_ratio - target_ar) / target_ar < aspect_ratio_tolerance:
            is_valid_aspect = True
            break
    
    if not is_valid_aspect:
        return False, actual_area_ratio, actual_aspect_ratio # Aspect ratio not in valid range

    return True, actual_area_ratio, actual_aspect_ratio


def ExtractSlidesToPDF(video_path: str = 'thevideo.mp4', output_path: str = 'slides.pdf', threshold: int = 2):
	"""Extracts unique slides from a video file and saves them into a PDF document.

	The process involves:
	1. Reading video frames one by one.
	2. Detecting potential slide content by cropping to the largest contour.
	3. Validating the cropped candidate based on size and aspect ratio.
	4. Comparing the current frame with the previous frame to detect significant changes.
	5. If a new, valid slide is detected, it's queued for saving as an image.
	6. Finally, all saved slide images are compiled into a single PDF.

	Args:
		video_path (str, optional): Path to the input video file. 
			Defaults to 'thevideo.mp4'.
		output_path (str, optional): Path where the output PDF will be saved. 
			Defaults to 'slides.pdf'.
		threshold (int, optional): Percentage change between frames to consider it a new slide. 
			Defaults to 2.
	"""
	
	if cv2.ocl.haveOpenCL():
		cv2.ocl.setUseOpenCL(True)
		print(f"OpenCL available: {cv2.ocl.haveOpenCL()}, Using OpenCL: {cv2.ocl.useOpenCL()}")
	else:
		print("OpenCL not available. Running on CPU.")

	threshold = threshold or 2
	video_path = video_path or 'thevideo.mp4'
	output_path = output_path or 'slides.pdf'

	print(f"Starting slide extraction from video: {video_path}")
	cap = cv2.VideoCapture(video_path)
	pdf = FPDF()
	image_list = []
	actual_slides_count = 0

	if (cap.isOpened()== False):
		print("Error opening video file")
		exit(1)

	with concurrent.futures.ThreadPoolExecutor() as executor:
		ret, frame = cap.read()
		if not ret:
			print("Error reading the first frame from video file")
			cap.release()
			exit(1)
		prev_frame = frame
		processed_frame = find_and_crop_slide(frame)

		is_valid_candidate, area_ratio, aspect_ratio = is_valid_slide_candidate(processed_frame, frame.shape)
		temp_image_path_debug = f'temp/temp{len(image_list)}.png'
		print(f"[DEBUG] Initial frame crop: {temp_image_path_debug}, Area Ratio: {area_ratio:.2f}, Aspect Ratio: {aspect_ratio:.2f}")

		if is_valid_candidate:
			temp_image_path = temp_image_path_debug
			print("Processing video frames...") 
			executor.submit(cv2.imwrite, temp_image_path, processed_frame)
			image_list.append(temp_image_path)
			actual_slides_count += 1
			print(f"Detected slide #{actual_slides_count} at first frame, queueing for save.")
		else:
			print(f"Initial frame crop skipped. Area Ratio: {area_ratio:.2f}, Aspect Ratio: {aspect_ratio:.2f}")


		counter = 0
		while(cap.isOpened()):
			counter += 1
			print(f"Processing frame {counter}...", end='\r')
			ret, frame = cap.read()
			if ret == True:
				if compare_frames(frame, prev_frame) > threshold: 
					slide_to_save = find_and_crop_slide(frame)

					is_valid_candidate, area_ratio, aspect_ratio = is_valid_slide_candidate(slide_to_save, frame.shape)
					temp_image_path_debug = f'temp/temp{len(image_list)}.png'
					print(f"[DEBUG] Frame {counter} crop: {temp_image_path_debug}, Area Ratio: {area_ratio:.2f}, Aspect Ratio: {aspect_ratio:.2f}")

					if is_valid_candidate:
						temp_image_path = temp_image_path_debug
						executor.submit(cv2.imwrite, temp_image_path, slide_to_save)
						image_list.append(temp_image_path)
						actual_slides_count += 1
						print(f"Detected slide #{actual_slides_count} at frame {counter}, queueing for save.")
						print(f"Processing frame {counter}...", end='\r') 
					else:
						print(f"Frame {counter} crop skipped. Area Ratio: {area_ratio:.2f}, Aspect Ratio: {aspect_ratio:.2f}. Processing frame {counter}...", end='\r')
				prev_frame = frame 
			else:
				break
		print() 
		print(f"Finished processing all frames. Total slides detected: {actual_slides_count}. Waiting for saves to complete...")
		executor.shutdown(wait=True)

	print(f"Generating PDF from {len(image_list)} slides...")
	for image in image_list:
		pdf.add_page()
		pdf.image(image, 0, 0, 210, 297)
		os.remove(image)

	pdf.output(output_path, "F")
	print(f"PDF generated successfully: {output_path}")
	cap.release()
	cv2.destroyAllWindows()

def initProgram():
	"""Handles user interaction to choose the source of the video (local file or YouTube) 
	and initiates the slide extraction process.
	"""
	print("Welcome to the Slide Extractor!")
	print("Please choose an option:")
	print("1. Extract Slides from Video (Local)")
	print("2. Extract video from youtube link")
	print("3. Exit")
	choice = input("Enter your choice: ")
	if choice == "1":
		threshold_input = input("Enter the threshold (default is 2): ")
		threshold = int(threshold_input) if threshold_input else 2
		video_path = input("Enter the video path: ")
		ExtractSlidesToPDF(threshold=threshold, video_path=video_path)
		print("Exported Slides Successfully")
		exit(0)
	if choice == "2":
		threshold_input = input("Enter the threshold (default is 2): ")
		threshold = int(threshold_input) if threshold_input else 2
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
	"""Parses command-line arguments and calls the appropriate functions 
	to download a video (if a YouTube link is provided) and extract slides.
	This function is the main entry point when the script is run with arguments.
	"""
	parser = argparse.ArgumentParser(description='Extracts slides from a video file or YouTube link.')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--youtube', '-y', metavar='<video_url>', help='URL of the YouTube video')
	group.add_argument('--file', '-f', metavar='<video_path>', help='Path to the local video file')
	parser.add_argument('--threshold', '-t', metavar='<value>', type=float, 
	                    help='Sensitivity for slide change detection (percentage, default: 2.0)')
	parser.add_argument('--output', '-o', metavar='<output_path>', 
	                    help='Path to save the output PDF file (default: slides.pdf)')

	args = parser.parse_args()

	# Set default values if not provided via CLI
	output_pdf_path = args.output if args.output else 'slides.pdf'
	# Threshold is handled by ExtractSlidesToPDF if None is passed

	if args.youtube:	
		Download(link=args.youtube)
		ExtractSlidesToPDF(threshold=args.threshold, video_path="temp/tempvideo.mp4", output_path=output_pdf_path)
		os.remove("temp/tempvideo.mp4")

	elif args.file:
		ExtractSlidesToPDF(threshold=args.threshold, video_path=args.file, output_path=output_pdf_path)
	else:
		# This case should ideally not be reached due to the mutually exclusive group being required.
		print('Invalid arguments or configuration. Please specify --youtube or --file.')
		parser.print_help()
		exit(1)

		



if __name__ == '__main__':
	# If the script is run with command-line arguments, main() will be called.
	# If run without arguments (e.g. python slide-extractor.py), 
	# it might be desirable to call initProgram() for interactive mode.
	# However, argparse will exit if required arguments are missing.
	# To enable interactive mode if no args, one might check len(sys.argv).
	# For now, standard argparse behavior is maintained.
	main()


