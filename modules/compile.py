#!/usr/bin/env python3
"""
Quinn Torres
qmt2002

usage: compile.py [-h] [--source-video-directory SOURCE_VIDEO_DIRECTORY]
                  [--reference-fps REFERENCE_FPS] [-s]
                  reference-directory

Compile a video of performances across different videos using a variety of
frames from the videos

positional arguments:
  reference-directory   the directory of directories of images (a folder
                        containing another folder called 'adjustments' and the
                        audio file 'audio.mp3') to use to compile the video

optional arguments:
  -h, --help            show this help message and exit
  --source-video-directory SOURCE_VIDEO_DIRECTORY
                        the directory of the folder to make a video from - if
                        none is specified, all folders in the reference-
                        directory create a video
  --reference-fps REFERENCE_FPS
                        the number of frames per second the images were
                        extracted at, to use as a reference
  -s                    stitch all videos in the reference-directory together
"""
import argparse
import random
import shutil
import subprocess
import datetime
import os

from termcolor import colored


def compile_videos(reference_directory, fps=12):
    """Compile multiple videos of random frames that match the original frames of each image directory in the parent directory

    Parameters
    ----------
    reference_directory : str
        the directory of directories containing adjusted images
    fps : int, optional
        how many frames were extracted per second of video for the adjusted source frames, by default 12
    """
    print(f"{colored('COMPILE:', 'blue')} Compiling videos from images in {reference_directory}\n")

    # Get an indexed dictionary of frames that can be used
    frame_dict = get_frame_dict(reference_directory)

    # Go through each item in the directory and use it for video compilation it if it's a folder
    for item in os.listdir(reference_directory):
        item_path = os.path.join(reference_directory, item)
        # Only use folders for compilation
        if os.path.isdir(item_path):
            compile_video(item_path, frame_dict=frame_dict, fps=fps)

    print(f"{colored('COMPILE:', 'blue')} Done compiling videos from images in {reference_directory}\n")


def compile_video(source_video_directory, reference_directory=None, frame_dict=None, fps=12):
    """Given a source directory of adjusted images, and a set of other directories of images, create a video of frames that match the source
    frames according to their open mouth ratio

    Parameters
    ----------
    source_video_directory : str
        the directory of images that will have matching frames found for them
    reference_directory : str, optional
        the directory of directories images that will be used for frame matches, by default None
        required if frame_dict is None
    frame_dict : dict{int: list[str]}, optional
        the dictionary of frame choice file paths, indexed by their mouth open ratio, by default None
        required if reference_directory is None
    fps : int, optional
        how many frames were extracted per second of video for the adjusted source frames, by default 12

    Raises
    ------
    Exception
        if there is both no reference_directory or frame_dict
    """
    print(f"{colored('COMPILE:', 'blue')} Compiling a video from images in {source_video_directory}")

    # Get an indexed dictionary of frames that can be used, if it doesn't exist yet (i.e. only one video being compiled)
    if frame_dict is None:
        if reference_directory is None:
            raise Exception("need either a dictionary of frames to use or a directory of videos to build the dictionary with")

        frame_dict = get_frame_dict(reference_directory)

    # Get a sorted list of all source video frames where the performer was recognized from
    # Have them separated into buckets of continuity where there are no jumps in frame count
    source_frame_buckets = get_source_frame_buckets(source_video_directory, fps)

    # Clear any old material
    buckets_directory = os.path.join(source_video_directory, "buckets")
    if os.path.isdir(buckets_directory):
        shutil.rmtree(buckets_directory)

    # Create a folder for the buckets of continuity and eventual video
    if not os.path.isdir(buckets_directory):
        os.mkdir(buckets_directory)

    # Iterate through each bucket of frames
    bucket_number = 1
    for bucket in source_frame_buckets:

        # Create a folder for each bucket
        bucket_directory = os.path.join(buckets_directory, str(bucket_number))
        os.mkdir(bucket_directory)

        # Create audio snippets within each bucket folder
        create_audio_snippet(bucket, bucket_number, source_video_directory, fps)

        # Iterate through each frame in the bucket
        frame_number = 1
        for frame in bucket:

            # Find a random matching frame for each frame in the bucket of continuity
            frame_path = os.path.join(bucket_directory, frame)
            random_frame_path = get_random_matching_frame(frame, frame_path, frame_dict)

            # Copy the frame over to the bucket folder
            copy_frame(random_frame_path, frame_number, bucket_directory)

            frame_number += 1

        bucket_number += 1

    # Compile each bucket into a video and then stitch them all into one video
    stitch_bucket_videos(buckets_directory, fps)

    print(f"{colored('COMPILE:', 'blue')} Done compiling a video from images in {source_video_directory}\n")


def create_audio_snippet(bucket, bucket_number, source_video_directory, fps):
    """Given a list of frames, create a snippet of the audio that plays during those frames

    Parameters
    ----------
    bucket : list[str]
        the list of images in the bucket, in the format framenumber_ratio.jpg
    bucket_number : int
        the number of the bucket, in order to save the snippet in the correct location
    source_video_directory : str
        the directory containing the adjusted source frames
    fps : int
        how many frames were extracted per second of video for the adjusted source frames
    """
    # Count how many frames there are in the entire video as a reference for how long the video was
    frame_count = 0
    for item in os.listdir(os.path.join(source_video_directory, "frames")):
        if item.endswith("jpg"):
            frame_count += 1

    # Grab the frame number from the beginning and ending frame count of the bucket
    start_frame_number = int(bucket[0].split("_")[0])
    end_frame_number = int(bucket[-1].split("_")[0])

    # Start/end time of the bucket clip in seconds is the frame number divided by frames per second
    # Subtract frame number by 1 because the audio starts when the frame starts, not when the frame ends
    audio_start_time_sec = (start_frame_number - 1) / fps
    audio_end_time_sec = (end_frame_number - 1) / fps
    audio_start_time = str(datetime.timedelta(seconds=audio_start_time_sec))
    audio_end_time = str(datetime.timedelta(seconds=audio_end_time_sec))

    # Audio that is being spliced and where to save the spliced audio to
    audio_input_path = os.path.join(source_video_directory, "audio.mp3")
    audio_output_path = os.path.join(source_video_directory, "buckets", str(bucket_number), "audio.mp3")

    subprocess.call(f"ffmpeg -i '{audio_input_path}' -ss '{audio_start_time}' -to '{audio_end_time}' -c copy '{audio_output_path}' -hide_banner -loglevel panic", shell=True)


def stitch_bucket_videos(bucket_directory, fps):
    """Go through each bucket folder in a directory and create small videos, and then stitch them all together

    Parameters
    ----------
    bucket_directory : str
        the directory where the bucket frames are stored
    fps : int
        how many frames were extracted per second of video for the adjusted source frames
    """
    print(f"{colored('COMPILE:', 'green')} Stitching all buckets in {bucket_directory}")

    # List all bucket videos for use with ffmpeg in concatenating them
    video_list_path = os.path.join(bucket_directory, "video_list.txt")
    stitched_videos_output_path = os.path.join(bucket_directory, "video.mp4")
    buckets_to_compile = []

    # Write to video_list.txt for each relevant bucket video
    with open(video_list_path, "w+") as video_list:

        # Compile the video in each bucket
        for item in os.listdir(bucket_directory):
            # Iterate through each bucket folder: 1, 2, ...
            item_path = os.path.join(bucket_directory, item)
            if os.path.isdir(item_path):
                buckets_to_compile.append(item_path)

        # Sort the list of bucket folder by bucket, so the video plays chronologically
        buckets_to_compile = sorted(buckets_to_compile, key=lambda filepath: int(filepath.split("/")[-1]))

        # Go through each bucket and compile the video
        for bucket_path in buckets_to_compile:

            # Save the compiled video in the bucket folder, along with the frames and audio
            bucket_video_output_path = os.path.join(bucket_path, "video.mp4")
            dynamic_images_path = os.path.join(bucket_path, "%05d.jpg")
            audio_snippet_path = os.path.join(bucket_path, "audio.mp3")

            # Compile the images and audio into a video, according to whichever is shortest
            # Tell ffmpeg the frames per second that the images were extracted at, so that that amount equals a second in the video
            subprocess.call(f"ffmpeg -r {fps} -i '{dynamic_images_path}' -i '{audio_snippet_path}' -c:v libx264 -c:a aac -vf 'pad=ceil(iw/2)*2:ceil(ih/2)*2' -pix_fmt yuv420p -crf 23 -r {fps} -shortest -y '{bucket_video_output_path}' -hide_banner -loglevel panic", shell=True)

            # Add the path to the video to the video list to be able to concatenate it later
            # File 'path/to/file.mp4'
            video_list.write(f"file '{bucket_video_output_path}'\n")

    # Stitch together the videos in each bucket
    subprocess.call(f"ffmpeg -f concat -safe 0 -i '{video_list_path}' -c copy '{stitched_videos_output_path}' -hide_banner -loglevel panic", shell=True)

    print(f"{colored('COMPILE:', 'green')} Done stitching all buckets in {bucket_directory}")


def stitch_all_videos(reference_directory):
    """Go through each bucket folder in a directory of directories of images and stitch all compiled bucket videos into one large video

    Parameters
    ----------
    reference_directory : str
        the directory of directories images that will be used for frame matches
    """
    print(f"{colored('COMPILE:', 'blue')} Stitching all videos in {reference_directory}")

    # List all compiled bucket videos for use with ffmpeg in concatenating them
    video_list_path = os.path.join(reference_directory, "video_list.txt")
    stitched_videos_output_path = os.path.join(reference_directory, "video.mp4")

    # Remove any previous video list or video
    if os.path.isfile(video_list_path):
        os.remove(video_list_path)
    if os.path.isfile(stitched_videos_output_path):
        os.remove(stitched_videos_output_path)

    # Write to video_list.txt for each relevant compiled bucket video
    with open(video_list_path, "w+") as video_list:

        # Iterate through all images/[video-id]/buckets/ folders
        for reference_item in os.listdir(reference_directory):

            # Check if there is a possible bucket directory
            bucket_directory = os.path.join(reference_directory, reference_item, "buckets")
            if os.path.isdir(bucket_directory):

                # Add the video to the ffmpeg concatenation list if one has been compiled
                bucket_video_path = os.path.join(bucket_directory, "video.mp4")
                if os.path.isfile(bucket_video_path):
                    video_list.write(f"file '{bucket_video_path}'\n")

    subprocess.call(f"ffmpeg -f concat -safe 0 -i '{video_list_path}' -c copy '{stitched_videos_output_path}' -hide_banner -loglevel panic", shell=True)

    print(f"{colored('COMPILE:', 'blue')} Done stitching all videos in {reference_directory}\n")


def get_frame_dict(reference_directory):
    """Return a dictionary, indexed by the mouth open ratio of the person in an image, pointing a list of filepaths of images with that ratio

    Parameters
    ----------
    reference_directory : str
        the directory of directories containing adjusted images

    Returns
    -------
    dict{int: list[str]}
        the ratio indexed dictionary of image filepaths
    """
    frame_dict = {}

    # Iterate through each folder of images in the directory
    for item in os.listdir(reference_directory):
        item_path = os.path.join(reference_directory, item)
        if os.path.isdir(item_path):
            reference_frame_directory = os.path.join(item_path, "adjustments")

            # Iterate through each image file in the "images/[video-id]/adjustments" directory
            for item in os.listdir(reference_frame_directory):
                if item.endswith("jpg"):
                    path_to_image = os.path.join(reference_frame_directory, item)

                    # Images are formatted as framenumber_ratio.jpg
                    # dict key: mouth open ratio (1 - 100)
                    # dict value: list of filepaths to image files with that ratio
                    mouth_open_ratio = int(item.split("_")[1].strip(".jpg"))
                    frame_dict.setdefault(mouth_open_ratio, []).append(path_to_image)

    return frame_dict


def get_source_frame_buckets(source_video_directory, fps):
    """Return a list of image names corresponding to frames that can be used as a reference in compiling a video.
    Segment the image names into their own separate list according to buckets where there is no large jump in the frame number

    Parameters
    ----------
    source_video_directory : str
        the directory containing the adjusted source frames
    fps : int
        how many frames were extracted per second of video for the adjusted source frames

    Returns
    -------
    list[[str]]
        a list of lists (buckets) of image files representing frames that are right after one another
    """
    source_frame_buckets = [[]]
    source_frames = []
    source_frame_directory = os.path.join(source_video_directory, "adjustments")

    # Gather an initial list of all images in the source video directory
    for item in os.listdir(source_frame_directory):
        if item.endswith("jpg"):
            source_frames.append(item)

    # Sort frame by frame number
    source_frames = sorted(source_frames, key=lambda frame_name: int(frame_name.split("_")[0]))

    # Start off the first bucket manually in order to have a previous frame to reference
    source_frame_buckets[0].append(source_frames[0])

    # Sort collections of frames into lists where there are no gaps in frame count
    for frame_name in source_frames[1:]:
        frame_number = int(frame_name.split("_")[0])
        # Frame number of the most recent frame in the most recent bucket
        previous_frame_number = int(source_frame_buckets[-1][-1].split("_")[0])

        # Allow for a one frame jump and just use the previous frame
        if frame_number == previous_frame_number + 2:
            source_frame_buckets[-1].append(source_frame_buckets[-1][-1])

        # Allow for a two frame jump and just use the previous frame twice
        if frame_number == previous_frame_number + 3:
            source_frame_buckets[-1].append(source_frame_buckets[-1][-1])
            source_frame_buckets[-1].append(source_frame_buckets[-1][-1])

        # Create a new bucket if there is a jump in the frame number greater than two
        elif frame_number > previous_frame_number + 3:
            source_frame_buckets.append([])

            # Remove the previous bucket if it amounts to less than half a second of video (fps / 2)
            if len(source_frame_buckets[-2]) < int(fps / 2):
                source_frame_buckets.pop(-2)

        source_frame_buckets[-1].append(frame_name)

    return source_frame_buckets


def get_random_matching_frame(frame, frame_path, frame_dict):
    """Find a random frame with the same mouth open ratio as the reference frame, using the frame dictionary

    Parameters
    ----------
    frame : str
        the file name of the frame
    frame_path : str
        the file path of the frame
    frame_dict : dict{int: list[str]}
        the dictionary of frame choice file paths, indexed by their mouth open ratio

    Returns
    -------
    dict{int: list[str]}
        the file path to the matching frame, or the original if no match could be found
    """
    # Default the matching frame to the frame itself, in case no match can be found
    matching_frame = frame_path
    mouth_open_ratio = int(frame.split("_")[1].strip(".jpg"))
    current_error = 0

    # Try to find a frame within an error range of +- 20, or else just return the frame itself
    while current_error < 20:
        current_ratio = mouth_open_ratio + current_error
        # Ratio is only between 1 and 100
        if not (current_ratio < 1 or current_ratio > 100):

            matching_options = frame_dict.get(current_ratio, [matching_frame])
            num_of_options = len(matching_options)

            # There are frames with the same mouth open ratio, within the current error
            # Additionally, it is not just the frame itself with no error
            if matching_options and not(current_error == 0 and num_of_options == 1):
                random_choice_index = random.randint(0, num_of_options - 1)
                possible_match = matching_options[random_choice_index]

                # Get the filename and make sure it isn't the file itself
                possible_match_name = possible_match.split("/")[-1]
                if possible_match_name != frame:
                    matching_frame = matching_options[random_choice_index]

        # No matching frame options
        # Incrementally increase the error, from 0 to 1, -1, 2, -2, 3, ...
        if current_error < 1:
            current_error -= 1
        current_error *= -1

    return matching_frame


def copy_frame(random_frame_path, frame_number, bucket_directory):
    """Copy a matching frame from its directory into the bucket of its match, and order it

    Parameters
    ----------
    random_frame_path : str
        the file path to the random matching frame
    frame_number : int
        the index of the frame in the sequence of the bucket, starting from 1
    bucket_directory : str
        the directory where the bucket frames are stored
    """
    # Pad the frame to format it correctly to later use in compiling the video
    # Each bucket has frames starting at 00001.jpg and continuing from there
    copy_frame_name = f"{str(frame_number).zfill(5)}.jpg"
    copy_frame_path = os.path.join(bucket_directory, copy_frame_name)

    # Copy the file from the directory where the random matching frame is into the correct bucket
    subprocess.call(f"cp '{random_frame_path}' '{copy_frame_path}'", shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile a video of performances across different videos using a variety of frames from the videos")
    parser.add_argument("reference-directory", help="the directory of directories of images (a folder containing another folder called 'adjustments' and the audio file 'audio.mp3') to use to compile the video")
    parser.add_argument("--source-video-directory", help="the directory of the folder to make a video from - if none is specified, all folders in the reference-directory create a video")
    parser.add_argument("--reference-fps", help="the number of frames per second the images were extracted at, to use as a reference", default=12)
    parser.add_argument("-s", action="store_true", help="stitch all videos in the reference-directory together")
    args = parser.parse_args()

    reference_directory = os.path.abspath(args.reference_directory)
    stitch_all = args.s

    # Create one video from one source
    if args.source_video_directory:
        source_video_directory = os.path.abspath(args.source_video_directory)
        compile_video(source_video_directory, reference_directory, fps=args.reference_fps)
    # Create multiple videos from multiple sources
    else:
        compile_videos(reference_directory, args.reference_fps)

    # Grab the compiled videos and make one long video in the directory above the reference_directory
    if stitch_all:
        stitch_all_videos(reference_directory)
