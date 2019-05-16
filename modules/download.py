#!/usr/bin/env python3
"""
Quinn Torres
qmt2002

usage: download.py [-h] [--quality QUALITY] video_url_file

Download YouTube videos from a text list of URLs

positional arguments:
  video_url_file     a text file with each line containing a youtube video url
                     to download

optional arguments:
  -h, --help         show this help message and exit
  --quality QUALITY  the maximum resolution of the videos, e.g. 240, 360, 720,
                     1080, by default 720
"""
import subprocess
import argparse
import os

from termcolor import colored


def get_list_of_urls(video_url_file):
    """Takes in a text file and returns a list of urls to download videos from

    Parameters
    ----------
    video_url_file : str
        the location of the text file to read from

    Returns
    -------
    list[str]
        a list of youtube urls to download videos from
    """
    list_of_urls = []

    # Iterate through each url and create a list
    with open(video_url_file, "r") as url_list:
        for url in url_list:
            url = url.strip()

            # Ignore comment lines starting with a #
            if url.startswith("#"):
                continue

            list_of_urls.append(url)

    return list_of_urls


def download_videos(video_url_file, list_of_urls, quality=720):
    """Creates a "video" directory and then download videos to it. Does not download a video if it already exists.

    Parameters
    ----------
    video_url_file: str
        the filepath to the video urls, to use as a relative place to download the videos to
    list_of_urls : list[str]
        a list of youtube urls to download videos from
    quality: int, optional
        the max resolution of video to download, by default 720
    """
    print(f"{colored('DOWNLOAD:', 'blue')} Downloading videos\n")

    # Create a "video" folder if it doesn't already exist
    directory_path = os.path.abspath(os.path.join(os.path.abspath(video_url_file), "..", "videos"))
    if not os.path.isdir(directory_path):
        os.mkdir(directory_path)

    # Download each video that isn't already in the folder
    for url in list_of_urls:
        print(f"{colored('DOWNLOAD:', 'green')} Downloading {url}")

        # Get a list of videos currently in the folder
        current_files = os.listdir(directory_path)
        is_duplicate = False

        # URLs are in the form https://www.youtube.com/watch?v=7ISn-ki81EI where 7ISn-ki81EI is the unique video id at the end of the video file name
        # Grab the video id from the url and check it against all current video files
        video_id = url.split("=")[1]
        for directory_file in current_files:
            if video_id in directory_file:
                is_duplicate = True
                print(f"{colored('DOWNLOAD:', 'yellow')} {video_id} already exists, not downloading\n")

        if not is_duplicate:
            # Download video using youtube-dl
            # Save file as [video-id].ext
            subprocess.call(f"youtube-dl {url} -f 'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]' -o '{directory_path}" + "/%(id)s.%(ext)s'", shell=True)
            print(f"{colored('DOWNLOAD:', 'green')} Done downloading {url}\n")

    print(f"{colored('DOWNLOAD:', 'blue')} Done downloading videos\n")


def download_video(url, quality=720):
    """Downloads a single video

    Parameters
    ----------
    url : str
        the url of the video to download
    quality: int, optional
        the max resolution of video to download, by default 720
    """
    download_videos([url], quality)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube videos from a text list of URLs")
    parser.add_argument("video-url-file", help="a text file with each line containing a youtube video url to download")
    parser.add_argument("--quality", help="the maximum resolution of the videos, e.g. 240, 360, 720, 1080, by default 720", default=720)
    args = parser.parse_args()

    list_of_urls = get_list_of_urls(args.video_url_file)
    download_videos(args.video_url_file, list_of_urls, args.quality)
