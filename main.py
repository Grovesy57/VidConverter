import argparse
import os
import shlex
import sys
import subprocess
from pathlib import Path

#TODO: Fix and implement batch conversions
#TODO: Test and verify single conversions
#TODO: Catch KeyboardInterrupt exceptions
#TODO: Investigate args.dry not running dry.

supported_formats = ('mp4', 'avi', 'mov', 'mkv', 'webm')
presets = ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "very slow")

# Argparse shit:
parser = argparse.ArgumentParser(
    prog="VidConverter",
    description="A tool for converting video files from the terminal using python",
    usage="%(prog)s [options] FILE_PATH"
)
parser.add_argument("source",
                    help="video file to convert (must be directory if using batch process mode).",
                    metavar="FILE_PATH"
                    )
parser.add_argument("-d", "--destination",
                    help="Specify where to place converted video(s). Default is the current working directory.",
                    default=os.getcwd()
                    )
parser.add_argument("-f", "--format",
                    help="Specify an output format. Default is mp4. Options are: " + ', '.join(supported_formats),
                    default="mp4",
                    choices=supported_formats,
                    metavar=""
                    )
parser.add_argument("-p", "--preset",
                    help="Specify an output speed and compression efficiency preset. Default is medium.",
                    default="medium",
                    choices=presets
                    )
parser.add_argument("-b", "--batch",
                    action="store_true",  # Evaluates false unless -b flag is parsed
                    help="Process all video files in the supplied FILE_PATH. Must be a directory."
                    )
parser.add_argument("-v", "--verbose",
                    action="store_true",
                    help="Prints a lot more detailed information during execution."
                    )
parser.add_argument("--dry",
                    action="store_true",
                    help="Runs the script without actually converting any video files."
                    )
args = parser.parse_args()


def batch_convert():

    if args.verbose:
        print("Running in batch mode")
        print()

    if not os.path.isdir(absolute_source):
        raise TypeError("Source file must be a directory when using batch process mode")

    images = []

    # Iterate through all files in the source directory to find files with .CR2 extension.
    for file in os.listdir(absolute_source):
        # Iterate over files contained in source directory. Maybe add recursion support later?
        absolute_file = build_source_path(file)
        if os.path.isfile(absolute_file):
            # Only iterate on file if it has a .CR2 extension
            splitter = file.split(".")
            if len(splitter) > 1 and splitter[-1] == "CR2":
                # Append file's absolute path to the list of images to process.
                images.append(absolute_file)

    # Exit early if no .CR2 Files were discovered in the source directory.
    if len(images) < 1:
        print("No Image files with a .CR2 extension were found in the provided source directory. Exiting..")
        sys.exit()

    for image_path in images:
        input_file = get_filename_with_extension(image_path)
        filename = input_file.split(".")[0]  # We don't need the extension this time around
        if not args.dry:
            convert(image_path, filename)


def build_output_path(filename):
    # Builds the destination filepath, filename, and appends the format extension for pillow.
    match os.name:
        case 'posix':  # For unix support
            return f"{absolute_destination}/{filename}.{args.format}"
        case 'nt':  # For windows support. Why can't you be normal with your file paths windows?!
            # Confusing as a motherfucker, but this f string SHOULD create a valid windows path in the output var
            # HOWEVER if you print the var, print will escape the first of each backslash.
            # i.e a var with C:\\Users\\user will be printed as C:\Users\user. Pretty sure both are valid?
            # os.getcwd() returns a path with double slashes, so lets just follow that principle.
            return f"{absolute_destination}\\{filename}.{args.format}"
        case _:
            raise OSError(f"os.name: '{os.name}' is not supported. Please report this on the github page!")


def build_source_path(filename):
    match os.name:
        case 'posix':
            return f"{absolute_source}/{filename}"
        case 'nt':
            return f"{absolute_source}\\{filename}"
        case _:
            raise OSError(f"os.name: '{os.name}' is not supported. Please report this on the github page!")


def convert(filepath, filename):

    print(f"Converting {filename} to {args.format}..")


    # Now lets convert it
    #TODO: Needs to become a subprocess for ffmpeg

    # Builds the destination filepath, filename, and appends the format extension.
    output = build_output_path(filename)

    # Test ffmpeg
    #TODO: Catch errors if ffmpeg fails to verify
    #TODO: Should only execute once. Here this is executing every convert.
    _result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True,
        check=True
    )
    ffmpeg_vers = _result.stdout.splitlines()[0]


    # Build the command for ffmpeg
    if (args.verbose):
        print()
        print("ffmpeg tested successfully and returned:")
        print(ffmpeg_vers)
        print()
        _log_level = "warning"
    else:
        _log_level = "error"

    command = [

        "ffmpeg",
        "-hide_banner",
        "-i", str(filepath),
        "-preset", args.preset,
        "-loglevel", _log_level,
        "-movflags", "+faststart",
        str(output)

    ]

    if not args.dry:
        try:
            # Writes the converted Video file to the output destination using the original Video name.
            #TODO: Yeah, this is where ffmpeg magic needs to happen.
            subprocess.run(command, check=True)

            if args.verbose:
                print(f"Conversion successful for {filename}")
                print(f"Output location: {output}")
                print()
        except OSError:
            print(f"Failed to save the converted Video. Do you have write permissions for the destination directory?")
            raise
    else:

        if args.verbose:
            print()
            print("Conversion was skipped due to --dry flag.")
            print()
            print("Conversion details if not for dry run:")
            print(f"Conversion File: {filename}")
            print(f"Output location: {output}")
            print()
            print(f"Complete ffmpeg command that was to be parsed:")
            print(shlex.join(command))
            print()

        else:
            print()
            print("Conversion was skipped due to --dry flag. Suggest adding -v for verbose output.")
            print()


def get_filename_with_extension(file_path):

    match os.name:
        case 'posix':  # For unix support
            return file_path.split("/")[-1]
        case 'nt':  # For windows support
            # TODO: Investigate this shit further, fuck you windows for using backslashes in your filepaths.
            return file_path.split("\\")[-1]


def single_convert():

    if args.verbose:
        print("Running in single mode")
        print()

    # Figure out the desired file at the end of the provided path (Will need to recurse this for batch process.)
    input_file = get_filename_with_extension(absolute_source)
    filename, extension = input_file.split(".")[0], input_file.split(".")[-1]

    # Raise an error if the source file isn't of a supported format
    if extension not in supported_formats:
        if os.path.isdir(absolute_source):
            raise TypeError("Source file is a directory, did you forget to pass the flag for batch mode? (-b)")
        else:
            raise TypeError("Source file is not a supported file type.")

    # Now lets convert it
    convert(absolute_source, filename)


if __name__ == "__main__":

    # Easier and safer to work with absolute paths in a lot of cases.
    absolute_source = os.path.abspath(args.source)
    absolute_destination = os.path.abspath(args.destination)

    if args.verbose:
        print()
        print("flag conditions:")
        print(f"dry run: {args.dry}")
        print(f"format: {args.format}")
        print(f"preset: {args.preset}")
        print()
        print(f"Source: {absolute_source}")
        print(f"Destination: {absolute_destination}")
        print(f"Using output format: {args.format}")
        print()

    # Raise an exception if the provided destination is not a directory.
    if not os.path.isdir(absolute_destination):
        raise TypeError("Destination must be a directory!")

    # Determine whether to execute in batch or single process mode
    single_convert() if not args.batch else batch_convert()