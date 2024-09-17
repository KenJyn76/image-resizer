import argparse
from ffmpeg_utils import ensure_ffmpeg_installed
from image_processing import probe, process_images
from file_utils import parse_size

def main():
    parser = argparse.ArgumentParser(description="Resize images to a target file size using FFmpeg.")
    parser.add_argument("input_folder", help="Folder containing images to resize")
    parser.add_argument("target_size", type=parse_size, help="Target file size (e.g., '500K', '5M', '2G')")
    parser.add_argument("--probe-only", action="store_true", help="Perform a probe without modifying files")
    args = parser.parse_args()

    ffmpeg_path, ffprobe_path = ensure_ffmpeg_installed()

    probe_results = probe(ffprobe_path, args.input_folder, args.target_size)

    if not args.probe_only:
        process_images(ffmpeg_path, probe_results)

if __name__ == "__main__":
    main()