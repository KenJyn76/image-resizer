import os
import sys
import subprocess
import hashlib
import requests
import shutil
from typing import Tuple

ASSETS_DIR = "assets"
FFMPEG_DIR = "ffmpeg-git-full"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z"
FFMPEG_SHA256_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z.sha256"
SEVEN_ZIP_URL = "https://www.7-zip.org/a/7zr.exe"

def install_package(package: str) -> None:
    print(f"Installing {package} library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
except ImportError:
    install_package("requests")
    import requests

def get_remote_sha256(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Warning: Failed to get remote SHA256. Error: {e}")
        return None

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, local_path: str) -> None:
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    downloaded_size = 0

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                downloaded_size += len(chunk)
                percent = int(50 * downloaded_size / total_size)
                sys.stdout.write(f"\r[{'=' * percent}{' ' * (50-percent)}] {downloaded_size}/{total_size} bytes")
                sys.stdout.flush()
    print("\nDownload completed.")

def verify_download(file_path: str) -> None:
    print("Verifying download...")
    remote_sha256 = get_remote_sha256(FFMPEG_SHA256_URL)

    if remote_sha256 is None:
        print("Skipping hash verification due to unavailable remote SHA256.")
        return

    local_sha256 = calculate_sha256(file_path)

    print(f"Remote SHA256: {remote_sha256}")
    print(f"Local SHA256:  {local_sha256}")

    if remote_sha256 != local_sha256:
        raise ValueError("Downloaded file hash does not match the expected hash.")
    print("Hash verification successful.")

def download_7zip() -> str:
    seven_zip_path = os.path.join(ASSETS_DIR, "7zr.exe")
    if not os.path.exists(seven_zip_path):
        print("Downloading 7-Zip standalone executable...")
        download_file(SEVEN_ZIP_URL, seven_zip_path)
    return seven_zip_path

def get_top_level_dir(seven_zip_path: str, archive_path: str) -> str:
    cmd = [seven_zip_path, "l", archive_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = result.stdout.split('\n')

    # Debugging output to see all lines returned
    print("Lines from 7-Zip listing:")
    for line in lines:
        print(line)

    # Look for the first directory in the listing
    for line in lines:
        if line.startswith("Path = ") and "D...." in line:  # Check for directory
            path = line.split("Path = ")[1].strip()
            top_level_dir = os.path.dirname(path)  # Get the directory of the path
            print(f"Identified top-level directory: {top_level_dir}")
            return top_level_dir  # Return the directory of the path

    raise ValueError("Unable to determine top-level directory in the archive")

def extract_ffmpeg(seven_zip_path: str, file_path: str) -> None:
    print("Extracting FFmpeg...")

    cmd = [seven_zip_path, "x", file_path, f"-o{ASSETS_DIR}", "-y"]
    subprocess.run(cmd, check=True, capture_output=True)
    print("Extraction completed.")

    # The expected extracted path is now directly the ASSETS_DIR
    extracted_path = os.path.join(ASSETS_DIR, "ffmpeg-2024-09-16-git-76ff97cef5-full_build")  # Update this to match the actual extracted folder name
    final_path = os.path.join(ASSETS_DIR, FFMPEG_DIR)

    if os.path.exists(final_path):
        shutil.rmtree(final_path)

    # Check if the extracted path exists before renaming
    if not os.path.exists(extracted_path):
        raise FileNotFoundError(f"Extracted path does not exist: {extracted_path}")

    os.rename(extracted_path, final_path)
    print(f"Renamed extracted directory to {FFMPEG_DIR}")

    os.remove(file_path)

def test_ffmpeg(ffmpeg_path: str, ffprobe_path: str) -> None:
    for exe_path, name in [(ffmpeg_path, "FFmpeg"), (ffprobe_path, "FFprobe")]:
        try:
            result = subprocess.run([exe_path, "-version"], capture_output=True, text=True, check=True)
            version_line = result.stdout.split('\n')[0]
            print(f"{name} version: {version_line}")
        except subprocess.CalledProcessError as e:
            print(f"Error running {name}: {e}")
            print(f"stderr: {e.stderr}")
            raise

def ensure_ffmpeg_installed() -> Tuple[str, str]:
    ffmpeg_path = os.path.join(ASSETS_DIR, FFMPEG_DIR, "bin", "ffmpeg.exe")
    ffprobe_path = os.path.join(ASSETS_DIR, FFMPEG_DIR, "bin", "ffprobe.exe")

    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        print("FFmpeg is already installed.")
    else:
        print("FFmpeg not found. Downloading...")
        os.makedirs(ASSETS_DIR, exist_ok=True)
        file_path = os.path.join(ASSETS_DIR, "ffmpeg.7z")

        try:
            download_file(FFMPEG_URL, file_path)
            print(f"Download completed. File size: {os.path.getsize(file_path)} bytes")

            verify_download(file_path)
            seven_zip_path = download_7zip()
            extract_ffmpeg(seven_zip_path, file_path)

            print("FFmpeg installation completed.")
        except Exception as e:
            print(f"Error during FFmpeg installation: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
        raise FileNotFoundError(f"FFmpeg or FFprobe executable not found at expected paths:\nffmpeg: {ffmpeg_path}\nffprobe: {ffprobe_path}")

    test_ffmpeg(ffmpeg_path, ffprobe_path)

    return ffmpeg_path, ffprobe_path