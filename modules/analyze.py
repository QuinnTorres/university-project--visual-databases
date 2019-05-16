#!/usr/bin/env python3
"""
Quinn Torres
qmt2002

usage: analyze.py [-h] [--examples EXAMPLES] [--model MODEL] [--images IMAGES]
                  [--sets-of-images SETS_OF_IMAGES] [-n]

Train on a set of faces and/or analyze a set of images for those faces

optional arguments:
  -h, --help            show this help message and exit
  --examples EXAMPLES   the directory of examples images (the model will be
                        saved in the same directory), containing a folder of
                        examples for each person to recognize
  --model MODEL         the pre-trained model to use in the analysis (*.clf)
  --images IMAGES       the directory of images (a folder containing another
                        folder called 'frames') to analyze (output saved in
                        analysis in the same directory) using a new or pre-
                        trained model
  --sets-of-images SETS_OF_IMAGES
                        the directory of directories of images (a folder
                        containing another folder called 'frames') to analyze
                        (output saved in analysis.txt in each directory) using
                        a new or pre-trained model
  -n                    instead of appending to any previous analysis.txt and
                        only analyzing new images, remove the output file and
                        start over again
"""
import collections
import pickle
import argparse
import statistics
import time
import datetime
import os

from modules.face_recognition_knn import train, predict
from termcolor import colored


def train_model(examples_path, model_save_path):
    """Train a K-Nearest Neighbors model on a set of example faces for each person to eventually recognize and save the model in the examples directory

    Parameters
    ----------
    examples_path : str
        The directory containing the folders which hold example pictures of each person's face
    model_save_path : str
        The path + filename of where to save the model, by default the example directory
    """
    print(f"{colored('ANALYZE:', 'blue')} Training model")
    train(examples_path, model_save_path)
    print(f"{colored('ANALYZE:', 'blue')} Done training model\n")


def analyze_images(images_path, model_path, clear_previous_analysis=False):
    """Analyze a directory of images for recognition of the faces trained in the model and output the analysis in analysis.txt in the images directory
    Text file format denoting the image, the person, and the bounding box for their face (possibly multiple lines per file, if multiple people in image):
    [image file name] ["<name of face recognized>" or "unknown" if unrecognized person] [face coordinate left] [fc top] [fc bottom] [fc right]
    Bouding box coordinates are only logged if a face is detected, otherwise line format is:
    [image file name] "none"

    Parameters
    ----------
    images_path : str
        The directory containing the images to analyze, which should contain a folder called "frames" holding all the images
    model_path : str
        The path + filename of where the model to use is saved
    clear_previous_analysis : bool, optional
        whether to only analyze images not in previous output, or clear the previous output and start fresh, by default False
    """
    print(f"{colored('ANALYZE:', 'blue')} Analyzing images in {images_path}/frames")

    # Set up paths to files and default variables
    analysis_output_path = os.path.join(images_path, "analysis.txt")
    frames_path = os.path.join(images_path, "frames")
    already_analyzed_images = []
    file_write_type = "a+"

    # Load the model
    loaded_model = None
    with open(model_path, 'rb') as model_file:
        loaded_model = pickle.load(model_file)

    # Clear previous analysis.txt if necessary
    if not clear_previous_analysis:
        already_analyzed_images = get_already_analyzed_images(analysis_output_path)
    else:
        file_write_type = "w+"

    # Write to analysis.txt
    with open(analysis_output_path, file_write_type) as analysis_output:

        # Track how many images have been analyzed already, and how long it takes
        file_list = sorted(os.listdir(frames_path))
        file_count = len(file_list)
        current_item_count = len(already_analyzed_images)

        # Build a FIFO list of analysis times to get an average
        analysis_time_list = collections.deque([], maxlen=50)

        # Iterate through each image
        for item in file_list:
            if item.endswith("jpg") and item not in already_analyzed_images:

                image_path = os.path.join(frames_path, item)

                # Calculate the time it takes to predict
                start_time = time.time()
                predictions = predict(image_path, knn_clf=loaded_model)
                end_time = time.time()

                # Add the most recent time it took to predict
                analysis_time_list.appendleft(end_time - start_time)

                # Calculate current progress and how much time is estimated to be left
                current_item_count += 1
                progress_percent = round((current_item_count / file_count) * 100, 3)
                avg_analysis_time = statistics.mean(analysis_time_list)
                est_time_left = str(datetime.timedelta(seconds=round((file_count - current_item_count) * avg_analysis_time, 3)))

                # Update on progress
                print(f"{colored('ANALYZE:', 'green')} Analyzed {item} in {str(datetime.timedelta(seconds=(end_time - start_time)))} | Progress: {progress_percent:.3f}% | Time left: {est_time_left}", end="\r")

                # Print and write predictions
                log_predictions(predictions, item, analysis_output)

    print(f"\n{colored('ANALYZE:', 'blue')} Done analyzing images in {images_path}/frames\n")


def analyze_sets_of_images(sets_of_images_path, model_path, clear_previous_analysis=False):
    """Analyze a directory of directories of images for recognition of the faces trained in the model and output the analysis in analysis.txt in the directory for each set of images

    Parameters
    ----------
    sets_of_images_path : str
        The directory containing the directories of images to analyze, which should then contain a folder called "frames" holding their images
    model_path : str
        The path + filename of where the model to use is saved
    clear_previous_analysis : bool, optional
        whether to only analyze images not in previous outputs, or clear the previous outputs and start fresh, by default False
    """
    print(f"{colored('ANALYZE:', 'blue')} Analyzing the sets of images in {sets_of_images_path}\n")

    # Go through each item in the directory and analyze it if it's a folder
    for item in os.listdir(sets_of_images_path):
        item_path = os.path.join(sets_of_images_path, item)
        # Only analyze folders
        if os.path.isdir(item_path):
            analyze_images(item_path, model_path, clear_previous_analysis)

    print(f"{colored('ANALYZE:', 'blue')} Done analyzing the sets of images in {sets_of_images_path}\n")


def get_already_analyzed_images(analysis_file_path):
    """Read a previously created analysis.txt and return a list of images that have already been analyzed

    Parameters
    ----------
    analysis_file_path : str
        File path to the analysis.txt file to read through

    Returns
    -------
    list : str
        a list of the names of the images that have already been analyzed
    """
    already_analyzed_images = []

    try:
        # Read through the analysis file
        with open(analysis_file_path, "r+") as analysis_file:
            previous_image_name = ""
            for line in analysis_file:
                # The name of the image file is the first entry on each line
                image_name = line.strip().split()[0]

                # Images may have multiple lines if there are multiple people, so only add an image name once
                if image_name != previous_image_name:
                    already_analyzed_images.append(image_name)

                previous_image_name = image_name

    # There might not be a previous analysis.txt, which is fine
    except FileNotFoundError:
        pass

    return already_analyzed_images


def log_predictions(predictions, item, analysis_output):
    """Write the given predications to an analysis file

    Parameters
    ----------
    predictions : list
        a list of people detected in an image, each in the format (name, (top, right, bottom, left)) [bounding box coordinates]
    item : str
        the name of the image file the predictions come from
    analysis_output : file
        the file stream to write to
    """

    prediction_output = f"{item} none\n"

    # Log prediction as
    # [image file name] ["<name of face recognized>" or "unknown" if unrecognized person] [face coordinate left] [fc top] [fc bottom] [fc right]
    if predictions:
        for name, (top, right, bottom, left) in predictions:
            prediction_output = f"{item} {name} {left} {top} {bottom} {right}\n"

    analysis_output.write(prediction_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train on a set of faces and/or analyze a set of images for those faces")
    parser.add_argument("--examples", help="the directory of examples images (the model will be saved in the same directory), containing a folder of examples for each person to recognize")
    parser.add_argument("--model", help="the pre-trained model to use in the analysis (*.clf)")
    parser.add_argument("--images", help="the directory of images (a folder containing another folder called 'frames') to analyze (output saved in analysis in the same directory) using a new or pre-trained model")
    parser.add_argument("--sets-of-images", help="the directory of directories of images (a folder containing another folder called 'frames') to analyze (output saved in analysis.txt in each directory) using a new or pre-trained model")
    parser.add_argument("-n", action="store_true", help="instead of appending to any previous analysis.txt and only analyzing new images, remove the output file and start over again")
    args = parser.parse_args()

    model_path = None
    clear_previous_analysis = args.n

    # Either train a new model or use a pre-trained one, not both
    if args.model and args.examples:
        parser.error("cannot specify a pre-trained model to use but also train a new model")

    # Cannot analyze both a single set of images and also multiple sets of images
    if args.images and args.sets_of_images:
        parser.error("either analyze a single set of images or multiple sets, not both")

    # If using a pre-trained model, necessary to analyze images or else the program has nothing to do
    if not (args.images or args.sets_of_images):
        parser.error("no images specified to analyze")

    # If analyzing images, need to have either a newly trained model or a pre-trained one
    if not (args.model or args.examples):
        parser.error("need a model to use for image analysis")

    # Use a pre-trained model
    if args.model:
        model_path = os.path.abspath(args.model)
    # Rain a new model and save it
    elif args.examples:
        examples_path = os.path.abspath(args.examples)
        model_save_path = os.path.join(examples_path, "model.clf")
        train_model(examples_path, model_save_path)
        model_path = model_save_path

    # Analyze a single set of images and save the analysis in analysis.txt
    if args.images:
        images_path = os.path.abspath(args.images)
        analyze_images(images_path, model_path, clear_previous_analysis)
    # Analyze multiple sets of images and the save the analysis in analysis.txt in each directory of images
    elif args.sets_of_images:
        sets_of_images_path = os.path.abspath(args.sets_of_images)
        analyze_sets_of_images(sets_of_images_path, model_path, clear_previous_analysis)
