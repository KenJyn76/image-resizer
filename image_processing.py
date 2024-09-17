import os
import json
import subprocess
import concurrent.futures
from typing import List, Tuple
from file_utils import estimate_scale_factor

def get_image_info(ffprobe_path: str, input_file: str) -> Tuple[int, int, int]:
    # ... (keep the existing implementation)

def process_file(ffprobe_path: str, input_file: str, target_size: int) -> Tuple[str, float, str]:
    # Indented block for process_file function
    # Add your code here

def probe(ffprobe_path: str, input_file: str) -> Dict[str, Any]:
    # Indented block for probe function
    # Add your code here

def resize_image(ffmpeg_path: str, input_file: str, output_file: str, scale_factor: float) -> str:
    # ... (keep the existing implementation)

def process_images(ffmpeg_path: str, probe_results: List[Tuple[str, float]]) -> None:
    # ... (keep the existing implementation)