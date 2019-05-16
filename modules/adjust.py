#!/usr/bin/env python3
"""
Quinn Torres
qmt2002

usage: adjust.py [-h] [--adjustments ADJUSTMENTS]
                 [--sets-of-adjustments SETS_OF_ADJUSTMENTS] [-c]
                 name

Use analyzation data to create new cropped and aligned images

positional arguments:
  name                  the name of the person (based on a folder of images in
                        the examples folder) to adjust images for

optional arguments:
  -h, --help            show this help message and exit
  --adjustments ADJUSTMENTS
                        the directory of images (a folder containing another
                        folder called 'frames') to adjust using the analysis
                        file within
  --sets-of-adjustments SETS_OF_ADJUSTMENTS
                        the directory of directories of images (a folder
                        containing another folder called 'frames') to adjust
                        using the analysis file within each directory
  -c                    instead of appending adjusted images to the
                        'adjustments' directory, clear it and start over
"""
import argparse
import math
import numpy
import shutil
import collections
import os
import time
import datetime
import statistics
import face_recognition

from PIL import Image
from termcolor import colored

X = 0
Y = 1


def adjust_images(images_path, name, clear=False):
    """Use the analysis file to crop and align images to the face of the person and save them in the "adjustments" directory

    Parameters
    ----------
    images_path : str
        the directory containing the analysis text file (analysis.txt) and the images to adjust (within the "frames" directory)
    name : str
        the name of the person (based on a folder of images in the examples folder) to adjust images for
    clear : bool, optional
        whether to clear out the "adjustments" folder and start over or not, by default False
    """
    print(f"{colored('ADJUST:', 'blue')} Adjusting images in {images_path}/frames, saving in {images_path}/adjustments")

    # Set up paths to files and default variables
    analysis_path = os.path.join(images_path, "analysis.txt")
    frames_path = os.path.join(images_path, "frames")
    adjustments_path = os.path.join(images_path, "adjustments")
    already_adjusted_images = {}

    # Clear previous images in the "adjustments" folder if necessary
    if not clear:
        already_adjusted_images = get_already_adjusted_images(adjustments_path)
    elif os.path.isdir(adjustments_path) and clear:
        shutil.rmtree(adjustments_path)

    # Create the "adjustments" folder if it doesn't already exist, or was just removed
    if not os.path.isdir(adjustments_path):
        os.mkdir(adjustments_path)

    # Create a dictionary of all relevant predictions indexed by the file name, in order to track progress
    analysis_dict = get_adjusted_analysis_dict(analysis_path, name)

    # Track how many images have been adjusted already, and how long it takes
    adjustment_count = len(analysis_dict)
    current_item_count = len(already_adjusted_images)

    # Build a FIFO list of adjustments times to get an average
    adjustment_time_list = collections.deque([], maxlen=50)

    # Iterate through each image which contains the relevant person
    for item in analysis_dict.keys():
        if item not in already_adjusted_images:

            image_path = os.path.join(frames_path, item)

            # Calculate the time it takes to predict
            start_time = time.time()
            bounding_box = analysis_dict[item]
            adjust(image_path, bounding_box, adjustments_path)
            end_time = time.time()

            # Add the most recent time it took to predict
            adjustment_time_list.appendleft(end_time - start_time)

            # Calculate current progress and how much time is estimated to be left
            current_item_count += 1
            progress_percent = round((current_item_count / adjustment_count) * 100, 3)
            avg_adjustment_time = statistics.mean(adjustment_time_list)
            est_time_left = str(datetime.timedelta(seconds=round((adjustment_count - current_item_count) * avg_adjustment_time, 3)))

            # Update on progress
            print(f"{colored('ADJUST:', 'green')} Adjusted {item} in {str(datetime.timedelta(seconds=(end_time - start_time)))} | Progress: {progress_percent:.3f}% | Time left: {est_time_left}", end="\r")

    print(f"\n{colored('ADJUST:', 'blue')} Done adjusting images in {images_path}/frames, saved in {images_path}/adjustments\n")


def adjust_sets_of_images(sets_of_images_path, name, clear=False):
    """Use the analysis file within each subdirectory to crop and align images to the face of the person and save them in the respective "adjustments" directories

    Parameters
    ----------
    sets_of_images_path : str
        the directory of directories containing the analysis text file (analysis.txt) and the images to adjust (within the "frames" directory)
    name : str
        the name of the person (based on a folder of images in the examples folder) to adjust images for
    clear : bool, optional
        whether to clear out the "adjustments" folder and start over or not, by default False
    """
    print(f"{colored('ADJUST:', 'blue')} Adjusting the sets of images in {sets_of_images_path}\n")

    # Go through each item in the directory and analyze it if it's a folder
    for item in os.listdir(sets_of_images_path):
        item_path = os.path.join(sets_of_images_path, item)
        # Only adjust folders
        if os.path.isdir(item_path):
            adjust_images(item_path, name, clear)

    print(f"{colored('ADJUST:', 'blue')} Done adjusting the sets of images in {sets_of_images_path}\n")


def get_already_adjusted_images(adjustments_path):
    """Looks through the "adjustments" directory and returns a list of images that have already been adjusted

    Parameters
    ----------
    adjustments_path : str
        File path to the "adjustments" folder to read through

    Returns
    -------
    list : str
        a list of the names of the images that have already been adjusted
    """
    already_adjusted_images = []

    # Look through each file in the directory
    if os.path.isdir(adjustments_path):
        for item in os.listdir(adjustments_path):
            if item.endswith("jpg"):
                # Remove the mouth open ratio on the end of the file name
                # Adjusted files are in the format 00000_00.jpg
                image_name = item.split("_")[0] + ".jpg"
                already_adjusted_images.append(image_name)

    return already_adjusted_images


def get_adjusted_analysis_dict(analysis_path, name):
    """Read in an analysis.txt file and convert it into a dictionry with file name keys and prediction values

    Parameters
    ----------
    analysis_path : str
        the filepath to the analysis.txt
    name : str
        the name of the person to adjust images for
    analysis_path : list[str]
        a list of file names of images that have already been adjusted

    Returns
    -------
    analysis_dict : dict
        A dictionary of images that have been analyzed, indexed by the file name
    """
    analysis_dict = {}

    with open(analysis_path, "r") as analysis:
        for line in analysis:
            line_data = line.strip().split()
            image_file_name = line_data[0]
            prediction_name = line_data[1]

            # Only index the file name if it's the relevant person being detected
            if prediction_name == name:
                left = int(line_data[2])
                top = int(line_data[3])
                bottom = int(line_data[4])
                right = int(line_data[5])

                bounding_box = (left, top, bottom, right)
                analysis_dict[image_file_name] = bounding_box

    return analysis_dict


def adjust(image_path, bounding_box, adjustments_path):
    """Crops and aligns an image according to facial landmark analysis, and saves the updated images into the "adjustments" folder

    Parameters
    ----------
    image_path : str
        the filepath to the image
    bounding_box : tuple(left, top, bottom, right)
        the bounding box of the face in the image
    adjustments_path : str
        the directory to save the image to
    """
    adjusted_image = Image.open(image_path)
    file_name = image_path.split("/")[-1]
    save_path = os.path.join(adjustments_path, file_name)

    # Crop to just the face
    adjusted_image = crop_image(adjusted_image, bounding_box)

    # Don't use this image if it was unreasonably small when cropped
    if not adjusted_image:
        return

    # Calculate how open the mouth is in relation to the width of the mouth, on a scale of 1 - 100
    mouth_open_ratio = get_mouth_open_ratio(adjusted_image)

    # Rotate to offset if the face is at an angle
    adjusted_image = rotate_image(adjusted_image)

    # Don't use this image if it couldn't be rotated
    if not adjusted_image:
        return

    # Put the mouth 2/3 vertically down and in the horizontal center
    adjusted_image = center_image(adjusted_image)

    # Don't use this image if it couldn't be centered
    if not adjusted_image:
        return

    # Resize all images to 300 x 300 (should already be squares from cropping)
    adjusted_image = resize_image(adjusted_image)

    # Set the image to grey (hard to process rapid color changes)
    adjusted_image = grayscale_image(adjusted_image)

    # Save with the mouth ratio appended on the end of the filename for easy indexing
    save_path = save_path.strip(".jpg") + f"_{mouth_open_ratio}.jpg"
    adjusted_image.save(save_path)


def crop_image(adjusted_image, bounding_box):
    """Crop the image to a person's face, dictated by the bounding_box

    Parameters
    ----------
    adjusted_image : Image
        the current image object
    bounding_box : tuple(left, top, bottom, right)
        the bounding box of the face in the image

    Returns
    -------
    Image
        the now-cropped image object
    """
    left = bounding_box[0]
    top = bounding_box[1]
    bottom = bounding_box[2]
    right = bounding_box[3]

    width = right - left
    height = bottom - top

    if width < 150 or height < 150:
        return

    # Crop into a square according to the larger of the two: width and height
    if width < height:
        diff = height - width
        left -= int(diff / 2)
        right += int(diff / 2)
    else:
        diff = width - height
        top -= int(diff / 2)
        bottom += int(diff / 2)

    adjusted_image = adjusted_image.crop([left, top, right, bottom])

    return adjusted_image


def rotate_image(adjusted_image):
    """Rotate the image using the angle of the eyebrows as a proxy for the face angle

    Parameters
    ----------
    adjusted_image : Image
        the current image object

    Returns
    -------
    Image
        the now-rotated image object
    """
    # Grab landmarks of the face
    landmarks = face_recognition.face_landmarks(numpy.array(adjusted_image))

    # Don't use the image if it can't be rotated
    if not landmarks:
        return

    # Sort eyebrow points by increasing x value (left to the right, of the viewer, in the video)
    left_eyebrow = sorted(landmarks[0]["left_eyebrow"], key=lambda point: point[X])
    right_eyebrow = sorted(landmarks[0]["right_eyebrow"], key=lambda point: point[X])

    # Left eyebrow (of the person) is on the right side of the video, right eyebrow is on the left side
    outer_left_eyebrow = left_eyebrow[-1]
    outer_right_eyebrow = right_eyebrow[1]

    # Calculate 3 points:
    # 1: A horizontal line starting at the outer left eyebrow and ending at the outer right eyebrow
    # 3: The outer left of their eyebrow
    # 2: The outer right of their eyebrow
    point_1 = (outer_left_eyebrow[X], outer_right_eyebrow[Y])
    point_2 = (outer_right_eyebrow[X], outer_right_eyebrow[Y])
    point_3 = (outer_left_eyebrow[X], outer_left_eyebrow[Y])

    # Get the angle between the 3 points as a measurement of how much the face is angled
    # Adapted from http://phrogz.net/angle-between-three-points
    a = pow(point_2[X] - point_1[X], 2) + pow(point_2[Y] - point_1[Y], 2)
    b = pow(point_2[X] - point_3[X], 2) + pow(point_2[Y] - point_3[Y], 2)
    c = pow(point_3[X] - point_1[X], 2) + pow(point_3[Y] - point_1[Y], 2)
    face_angle = math.degrees(math.acos((a + b - c) / math.sqrt(4 * a * b)))

    # Rotate to offset face angle
    adjusted_image = adjusted_image.rotate(-face_angle)

    return adjusted_image


def center_image(adjusted_image):
    """Translate the image in order to position the mouth at a specific spot

    Parameters
    ----------
    adjusted_image : Image
        the current image object

    Returns
    -------
    Image
        the now-translated image object
    """
    # Grab landmarks of the face
    landmarks = face_recognition.face_landmarks(numpy.array(adjusted_image))

    # Don't use the image if it can't be centered
    if not landmarks:
        return

    bottom_lip = landmarks[0]["bottom_lip"]
    top_lip = landmarks[0]["top_lip"]

    # Calculate highest and lowest X and Y values of the mouth
    top_of_lip = min(top_lip, key=lambda point: point[Y])[Y]
    bottom_of_lip = max(bottom_lip, key=lambda point: point[Y])[Y]
    left_of_lip = min(min(top_lip, key=lambda point: point[X])[X], min(bottom_lip, key=lambda point: point[X])[X])
    right_of_lip = max(max(top_lip, key=lambda point: point[X])[X], max(bottom_lip, key=lambda point: point[X])[X])

    # Set goal mouth position as the center of the bounding box 2/3 down vertically and in the center
    image_width, image_height = adjusted_image.size
    mouth_goal = (int(image_width / 2), int(image_height * (2 / 3)))

    # Calculate current mouth center
    mouth_center = (int((left_of_lip + right_of_lip) / 2), int((top_of_lip + bottom_of_lip) / 2))

    # Calculate image transformation
    horizontal_translation = mouth_goal[X] - mouth_center[X]
    vertical_translation = mouth_goal[Y] - mouth_center[Y]

    # Transformed according to (ax+by+c, dx+ey+f)
    # (a, b, c, d, e, f)
    # a = 1 to start at current x pixel
    # e = 1 to start at current y pixel
    # c = horizontal_translation
    # f = vertical_translation
    adjusted_image = adjusted_image.transform(adjusted_image.size, Image.AFFINE, (1, 0, -horizontal_translation, 0, 1, -vertical_translation))

    return adjusted_image


def resize_image(adjusted_image):
    """Resize the image (which should already be a square) to a constant size

    Parameters
    ----------
    adjusted_image : Image
        the current image object

    Returns
    -------
    Image
        the now-resized image object
    """
    size = (300, 300)
    return adjusted_image.resize(size)


def grayscale_image(adjusted_image):
    """Convert the image to grayscale

    Parameters
    ----------
    adjusted_image : Image
        the current image object

    Returns
    -------
    Image
        the now-gray image object
    """
    return adjusted_image.convert("L")


def get_mouth_open_ratio(adjusted_image):
    """Calculate the ratio between how open the mouth is and the width of the mouth, and return an int on a scale from 1 - 100

    Parameters
    ----------
    adjusted_image : Image
        the current image object

    Returns
    -------
    int
        a value 1 - 100 designating how open the mouth is, relatively
    """
    # Grab landmarks of the face
    landmarks = face_recognition.face_landmarks(numpy.array(adjusted_image))

    # Don't use the image if the mouth open ratio can't be calculated
    if not landmarks:
        return

    # Sort lip points by increasing x value (left to the right, of the viewer, in the video)
    bottom_lip = sorted(landmarks[0]["bottom_lip"], key=lambda point: point[X])
    top_lip = sorted(landmarks[0]["top_lip"], key=lambda point: point[X])

    # Set left, middle, and right points of the bottom lip
    left_of_bottom_lip = bottom_lip[0]
    middle_of_bottom_lip = bottom_lip[int(len(bottom_lip) / 2)]
    right_of_bottom_lip = bottom_lip[-1]

    # Set left, middle, and right points of the top lip
    left_of_top_lip = top_lip[0]
    middle_of_top_lip = top_lip[int(len(top_lip) / 2)]
    right_of_top_lip = top_lip[-1]

    # Calculate euclidean distance between left side of lip and right side of lip to get lip width
    # Average the top and bottom values
    bottom_lip_width = math.hypot(right_of_bottom_lip[X] - left_of_bottom_lip[X], right_of_bottom_lip[Y] - left_of_bottom_lip[Y])
    top_lip_width = math.hypot(right_of_top_lip[X] - left_of_top_lip[X], right_of_top_lip[Y] - left_of_top_lip[Y])
    lip_width = (bottom_lip_width + top_lip_width) / 2

    # Calculate euclidean distance between the middle of the top and bottom lip
    open_mouth_height = math.hypot(middle_of_top_lip[X] - middle_of_bottom_lip[X], middle_of_top_lip[Y] - middle_of_bottom_lip[Y])

    # Ratio of how open the mouth is to the width of the mouth, 1 - 100
    # Ratio of 0.46 => 46
    mouth_open_ratio = min(max(int((open_mouth_height / lip_width) * 100), 1), 100)

    return mouth_open_ratio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use analyzation data to create new cropped and aligned images")
    parser.add_argument("name", help="the name of the person (based on a folder of images in the examples folder) to adjust images for")
    parser.add_argument("--adjustments", help="the directory of images (a folder containing another folder called 'frames') to adjust using the analysis file within")
    parser.add_argument("--sets-of-adjustments", help="the directory of directories of images (a folder containing another folder called 'frames') to adjust using the analysis file within each directory")
    parser.add_argument("-c", action="store_true", help="instead of appending adjusted images to the 'adjustments' directory, clear it and start over")
    args = parser.parse_args()

    clear_adjustments_directory = args.c

    # Cannot adjust only a set of images but also a set of sets of images
    if args.adjustments and args.sets_of_adjustments:
        parser.error("either adjust a single set of images or multiple sets, not both")

    # Necessary to have a folder of images to adjust or else the program has nothing to do
    if not (args.adjustments or args.sets_of_adjustments):
        parser.error("no images specified to adjust")

    # Adjust a single set of images and save them in a folder named "adjustments"
    if args.adjustments:
        images_path = os.path.abspath(args.adjustments)
        adjust_images(images_path, args.name, clear_adjustments_directory)
    # Adjust multiple sets of images and save them in a folder named "adjustments" in each directory
    elif args.sets_of_adjustments:
        sets_of_images_path = os.path.abspath(args.sets_of_adjustments)
        adjust_sets_of_images(sets_of_images_path, args.name, clear_adjustments_directory)
