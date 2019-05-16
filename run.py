#!/usr/bin/env python3
"""
usage: run.py [-h] [--video-url-file VIDEO_URL_FILE] [--quality QUALITY]
              [--video-directory VIDEO_DIRECTORY] [--fps FPS]
              [--qscale QSCALE] [--examples EXAMPLES] [--model MODEL]
              [--images IMAGES] [--sets-of-images SETS_OF_IMAGES] [-n]
              [--name NAME] [--adjustments ADJUSTMENTS]
              [--sets-of-adjustments SETS_OF_ADJUSTMENTS] [-c]
              [--reference-directory REFERENCE_DIRECTORY]
              [--source-video-directory SOURCE_VIDEO_DIRECTORY]
              [--reference-fps REFERENCE_FPS] [-s]

Analyze videos for an artist's face and use it create a new video. There are
five steps: DOWNLOAD, CONVERT, ANALYZE, ADJUST, and COMPILE. Any of these can
be run.

optional arguments:
  -h, --help            show this help message and exit
  --video-url-file VIDEO_URL_FILE
                        (required, DOWNLOAD) a text file with each line
                        containing a youtube video url to use in the project
  --quality QUALITY     (optional, DOWNLOAD) the maximum resolution of the
                        videos, e.g. 240, 360, 720, 1080, by default 720
  --video-directory VIDEO_DIRECTORY
                        (required, CONVERT) the directory of videos to convert
                        into individual frames
  --fps FPS             (optional, CONVERT) the number of frames to convert
                        per second of video, by default 12
  --qscale QSCALE       (optional, CONVERT) the quality of the frames, 2 being
                        the lowest and 31 the highest, by default 12
  --examples EXAMPLES   (optional if no --model, ANALYZE) the directory of
                        examples images (the model will be saved in the same
                        directory), containing a folder of examples for each
                        person to recognize
  --model MODEL         (optional if no --examples, ANALYZE) the pre-trained
                        model to use in the analysis (*.clf)
  --images IMAGES       (required if no --sets-of-images, ANALYZE) the
                        directory of images to analyze (output saved in
                        analysis in the same directory) using a new or pre-
                        trained model
  --sets-of-images SETS_OF_IMAGES
                        (required if no --images, ANALYZE) the directory of
                        directories of images to analyze (output saved in
                        analysis.txt in each directory) using a new or pre-
                        trained model
  -n                    (optional, ANALYZE) instead of appending to any
                        previous analysis.txt and only analyzing new images,
                        remove the output file and start over again
  --name NAME           (required, ADJUST) the name of the person (based on a
                        folder of images in the examples folder) to adjust
                        images for
  --adjustments ADJUSTMENTS
                        (required if no --sets-of-adjustments, ADJUST) the
                        directory of images (a folder containing another
                        folder called 'frames') to adjust using the analysis
                        file within
  --sets-of-adjustments SETS_OF_ADJUSTMENTS
                        (required if no --adjustments, ADJUST) the directory
                        of directories of images (a folder containing another
                        folder called 'frames') to adjust using the analysis
                        file within each directory
  -c                    (optional, ADJUST) instead of appending adjusted
                        images to the 'adjustments' directory, clear it and
                        start over
  --reference-directory REFERENCE_DIRECTORY
                        (required, COMPILE) the directory of directories of
                        images (a folder containing another folder called
                        'adjustments' and the audio file 'audio.mp3') to use
                        to compile the video
  --source-video-directory SOURCE_VIDEO_DIRECTORY
                        (optional, COMPILE) the directory of the folder to
                        make a video from - if none is specified, all folders
                        in the reference-directory create a video
  --reference-fps REFERENCE_FPS
                        (optional, COMPILE) the number of frames per second
                        the images were extracted at, to use as a reference
  -s                    (optional, COMPILE) stitch all videos in the
                        reference-directory together
"""
import argparse
import os

from modules import download, convert, analyze, adjust, compile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze videos for an artist's face and use it create a new video. There are five steps: DOWNLOAD, CONVERT, ANALYZE, ADJUST, and COMPILE. Any of these can be run.")

    # 1. Download files
    parser.add_argument("--video-url-file", help="(required, DOWNLOAD) a text file with each line containing a youtube video url to use in the project")
    parser.add_argument("--quality", help="(optional, DOWNLOAD) the maximum resolution of the videos, e.g. 240, 360, 720, 1080, by default 720", default=720)

    # 2. Convert to images
    parser.add_argument("--video-directory", help="(required, CONVERT) the directory of videos to convert into individual frames")
    parser.add_argument("--fps", help="(optional, CONVERT) the number of frames to convert per second of video, by default 12", default=12)
    parser.add_argument("--qscale", help="(optional, CONVERT) the quality of the frames, 2 being the lowest and 31 the highest, by default 12", default=2)

    # 3. Analyze images
    parser.add_argument("--examples", help="(optional if no --model, ANALYZE) the directory of examples images (the model will be saved in the same directory), containing a folder of examples for each person to recognize")
    parser.add_argument("--model", help="(optional if no --examples, ANALYZE) the pre-trained model to use in the analysis (*.clf)")
    parser.add_argument("--images", help="(required if no --sets-of-images, ANALYZE) the directory of images to analyze (output saved in analysis in the same directory) using a new or pre-trained model")
    parser.add_argument("--sets-of-images", help="(required if no --images, ANALYZE) the directory of directories of images to analyze (output saved in analysis.txt in each directory) using a new or pre-trained model")
    parser.add_argument("-n", action="store_true", help="(optional, ANALYZE) instead of appending to any previous analysis.txt and only analyzing new images, remove the output file and start over again")

    # 4. Adjust images
    parser.add_argument("--name", help="(required, ADJUST) the name of the person (based on a folder of images in the examples folder) to adjust images for")
    parser.add_argument("--adjustments", help="(required if no --sets-of-adjustments, ADJUST) the directory of images (a folder containing another folder called 'frames') to adjust using the analysis file within")
    parser.add_argument("--sets-of-adjustments", help="(required if no --adjustments, ADJUST) the directory of directories of images (a folder containing another folder called 'frames') to adjust using the analysis file within each directory")
    parser.add_argument("-c", action="store_true", help="(optional, ADJUST) instead of appending adjusted images to the 'adjustments' directory, clear it and start over")

    # 5. Compile video
    parser.add_argument("--reference-directory", help="(required, COMPILE) the directory of directories of images (a folder containing another folder called 'adjustments' and the audio file 'audio.mp3') to use to compile the video")
    parser.add_argument("--source-video-directory", help="(optional, COMPILE) the directory of the folder to make a video from - if none is specified, all folders in the reference-directory create a video")
    parser.add_argument("--reference-fps", help="(optional, COMPILE) the number of frames per second the images were extracted at, to use as a reference", default=12)
    parser.add_argument("-s", action="store_true", help="(optional, COMPILE) stitch all videos in the reference-directory together")

    args = parser.parse_args()

    # 1. Download files

    if args.video_url_file:
        list_of_urls = download.get_list_of_urls(args.video_url_file)
        download.download_videos(args.video_url_file, list_of_urls, args.quality)

    # 2. Convert to images

    if args.video_directory:
        video_directory = os.path.abspath(args.video_directory)
        convert.convert_directory(video_directory, args.fps, args.qscale)

    # 3. Analyze images

    model_path = None
    clear_previous_analysis = args.n

    if args.model:
        model_path = os.path.abspath(args.model)
    elif args.examples:
        examples_path = os.path.abspath(args.examples)
        model_save_path = os.path.join(examples_path, "model.clf")
        analyze.train_model(examples_path, model_save_path)
        model_path = model_save_path

    if args.images:
        images_path = os.path.abspath(args.images)
        analyze.analyze_images(images_path, model_path, clear_previous_analysis)
    elif args.sets_of_images:
        sets_of_images_path = os.path.abspath(args.sets_of_images)
        analyze.analyze_sets_of_images(sets_of_images_path, model_path, clear_previous_analysis)

    # 4. Adjust images

    clear_adjustments_directory = args.c

    # Adjust a single set of images and save them in a folder named "adjustments"
    if args.adjustments:
        images_path = os.path.abspath(args.adjustments)
        adjust.adjust_images(images_path, args.name, clear_adjustments_directory)
    # Adjust multiple sets of images and save them in a folder named "adjustments" in each directory
    elif args.sets_of_adjustments:
        sets_of_images_path = os.path.abspath(args.sets_of_adjustments)
        adjust.adjust_sets_of_images(sets_of_images_path, args.name, clear_adjustments_directory)

    # 5. Compile video

    stitch_all = args.s

    # Create one video from one source
    if args.source_video_directory:
        source_video_directory = os.path.abspath(args.source_video_directory)
        reference_directory = os.path.abspath(args.reference_directory)
        compile.compile_video(source_video_directory, reference_directory, fps=args.reference_fps)
    # Create multiple videos from multiple sources
    elif args.reference_directory:
        reference_directory = os.path.abspath(args.reference_directory)
        compile.compile_videos(reference_directory, args.reference_fps)

    # Grab the compiled videos and make one long video in the directory above the reference_directory
    if stitch_all:
        compile.stitch_all_videos(reference_directory)   
