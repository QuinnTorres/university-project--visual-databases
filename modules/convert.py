#!/usr/bin/env python3
"""
Quinn Torres
qmt2002

usage: convert.py [-h] [--fps FPS] [--qscale QSCALE] video_directory

Convert a folder of videos into folders of individual frames

positional arguments:
  video_directory  the directory of videos to convert into individual frames

optional arguments:
  -h, --help       show this help message and exit
  --fps FPS        the number of frames to convert per second of video, by
                   default 12
  --qscale QSCALE  the quality of the frames, 2 being the lowest and 31 the
                   highest, by default 12
"""
import argparse
import os
import subprocess

from termcolor import colored


def convert_directory(video_directory, fps=12, qscale=2):
    """Convert a directory of videos into individual frames at the specified fps and the separated audio track

    Parameters
    ----------
    video_directory : str
        the path to the video directory
    fps : int, optional
        how many frames to extract per second of every video, by default 12
    qscale : int, optional
        the quality of the image, 2 being the highest and 31 being the lowest, by default 2
    """

    # Create an "images" folder if it doesn't already exist
    # "images" folder should be a sibling of the "videos" folder
    images_directory = os.path.abspath(os.path.join(video_directory, "..", "images"))
    if not os.path.isdir(images_directory):
        os.mkdir(images_directory)

    print(f"{colored('CONVERT:', 'blue')} Converting video directory\n")

    # Iterate through video files and convert
    for directory_file in os.listdir(video_directory):
        # Only attempt to convert compatible videos
        if directory_file.endswith("mkv") or directory_file.endswith("webm") or directory_file.endswith("mp4"):
            convert_video(video_directory, directory_file, fps, qscale)

    print(f"{colored('CONVERT:', 'blue')} Done converting video directory\n")


def convert_video(video_directory, video_file, fps=12, qscale=2):
    """Convert a video into individual frames at the specified fps and a separated audio track

    Parameters
    ----------
    video_directory : str
        path to the directory of videos
    video : str
        name of the video to convert
    fps : int, optional
        how many frames to extract per second of video, by default 12
    qscale : int, optional
        the quality of the image, 2 being the highest and 31 being the lowest, by default 2
    """
    print(f"{colored('CONVERT:', 'green')} Converting {video_file}")

    # Set paths for where to save the images
    images_directory = os.path.abspath(os.path.join(video_directory, "..", "images"))
    video_file_folder = video_file.split(".")[0]  # grab the video id of the video (format is 2lTB1pIg1y0.mkv)
    video_output_directory = os.path.join(images_directory, video_file_folder, "frames")  # directory is [project_folder]/images/[video_id]/frames
    audio_output_directory = os.path.join(images_directory, video_file_folder, "audio.mp3")  # direcotry is [project_folder]/images/[video_id]/audio.mp3
    video_file_path = os.path.join(video_directory, video_file)

    # Video has not already been converted, so it doesn't have a folder in the "images" directory
    if not os.path.isdir(video_output_directory):
        os.makedirs(video_output_directory)

        # Convert video to frames
        subprocess.call(f"ffmpeg -i '{video_file_path}' -vf fps={fps} -qscale:v {qscale} '{video_output_directory}/%05d.jpg' -hide_banner -loglevel panic", shell=True)

        # Convert video to audio
        subprocess.call(f"ffmpeg -i '{video_file_path}' -f mp3 -ab 192000 -vn '{audio_output_directory}' -hide_banner -loglevel panic", shell=True)

        print(f"{colored('CONVERT:', 'green')} Done converting {video_file}\n")

    else:
        print(f"{colored('CONVERT:', 'yellow')} {video_file} already has images, not converting\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a folder of videos into folders of individual frames and separated audio tracks")
    parser.add_argument("video-directory", help="the directory of videos to convert into individual frames")
    parser.add_argument("--fps", help="the number of frames to convert per second of video, by default 12", default=12)
    parser.add_argument("--qscale", help="the quality of the frames, 2 being the lowest and 31 the highest, by default 12", default=2)
    args = parser.parse_args()

    video_directory = os.path.abspath(args.video_directory)

    convert_directory(video_directory, args.fps, args.qscale)
