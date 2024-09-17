import os
import sys
import subprocess
import hashlib
import requests
import shutil
import zipfile
from typing import Tuple

ASSETS_DIR = "assets"
FFMPEG_DIR = "ffmpeg-git-full"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_SHA256_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip.sha256"

def install_package(package: str) -> None:
    print(f"Installing {package} library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
except ImportError:
    install_package("requests")
    import requests

def get_remote_sha256(url: str) -> str:
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to get remote SHA256. Status code: {response.status_code}")
    return response.text.strip()

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

def verify_download(zip_path: str) -> None:
    print("Verifying download...")
    remote_sha256 = get_remote_sha256(FFMPEG_SHA256_URL)
    local_sha256 = calculate_sha256(zip_path)

    print(f"Remote SHA256: {remote_sha256}")
    print(f"Local SHA256:  {local_sha256}")

    if remote_sha256 != local_sha256:
        raise ValueError("Downloaded file hash does not match the expected hash.")
    print("Hash verification successful.")

def extract_ffmpeg(zip_path: str) -> None:
    print("Extracting FFmpeg...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(ASSETS_DIR)
    print("Extraction completed.")
    os.remove(zip_path)

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
        zip_path = os.path.join(ASSETS_DIR, "ffmpeg.zip")

        try:
            download_file(FFMPEG_URL, zip_path)
            print(f"Download completed. File size: {os.path.getsize(zip_path)} bytes")

            verify_download(zip_path)
            extract_ffmpeg(zip_path)

            print("FFmpeg installation completed.")
        except Exception as e:
            print(f"Error during FFmpeg installation: {e}")
            raise

    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
        raise FileNotFoundError(f"FFmpeg or FFprobe executable not found at expected paths:\nffmpeg: {ffmpeg_path}\nffprobe: {ffprobe_path}")

    test_ffmpeg(ffmpeg_path, ffprobe_path)

    return ffmpeg_path, ffprobe_path