import argparse
from ffmpeg_utils import ensure_ffmpeg_installed
from image_processing import process_file_sizes, probe, process_images
from file_utils import parse_size

def main():
    """Main function to handle command-line arguments and initiate image processing."""
    parser = argparse.ArgumentParser(description="Resize images to a target file size using FFmpeg.")
    parser.add_argument("input_folder", help="Folder containing images to resize")  # Input folder argument
    parser.add_argument("target_size", type=parse_size, help="Target file size (e.g., '500K', '5M', '2G')")  # Target size argument
    parser.add_argument("--probe-only", action="store_true", help="Perform a probe without modifying files")  # Probe-only flag
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")  # Verbose flag
    args = parser.parse_args()  # Parse command-line arguments

    if args.target_size is None:  # Check if target_size is None
        raise ValueError("Target size cannot be None. Please provide a valid size.")

    ffmpeg_path, ffprobe_path = ensure_ffmpeg_installed()  # Ensure FFmpeg is installed

    # Process file sizes first
    files_to_process = process_file_sizes(args.input_folder, args.target_size, args.verbose)

    # Now probe the images that need processing
    probe_results = probe(ffprobe_path, files_to_process, args.target_size, args.verbose)  # Pass target_size

    # If not in probe-only mode, process the images
    if not args.probe_only:
        process_images(ffmpeg_path, probe_results, args.verbose)

if __name__ == "__main__":
    main()  # Run the main function