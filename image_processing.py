import os
import json
import subprocess
import concurrent.futures
from typing import List, Tuple, Dict, Any
from file_utils import estimate_scale_factor

def get_image_info(ffprobe_path: str, input_file: str) -> Tuple[int, int, int]:
    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    width = int(data['streams'][0]['width'])
    height = int(data['streams'][0]['height'])
    size = int(data['format']['size'])

    return width, height, size

def process_file(ffprobe_path: str, input_file: str, target_size: int) -> Tuple[str, float, str]:
    width, height, current_size = get_image_info(ffprobe_path, input_file)
    scale_factor = estimate_scale_factor(current_size, target_size)
    output_file = f"resized_{os.path.basename(input_file)}"
    return input_file, scale_factor, output_file

def probe(ffprobe_path: str, input_folder: str, target_size: int) -> List[Tuple[str, float, str]]:
    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, ffprobe_path, file, target_size) for file in image_files]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    return results

def resize_image(ffmpeg_path: str, input_file: str, output_file: str, scale_factor: float) -> str:
    cmd = [
        ffmpeg_path,
        "-i", input_file,
        "-vf", f"scale=iw*{scale_factor}:ih*{scale_factor}",
        "-y",
        output_file
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_file

def process_images(ffmpeg_path: str, probe_results: List[Tuple[str, float, str]]) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(resize_image, ffmpeg_path, input_file, output_file, scale_factor)
                   for input_file, scale_factor, output_file in probe_results]
        concurrent.futures.wait(futures)

    print("Image processing completed.")