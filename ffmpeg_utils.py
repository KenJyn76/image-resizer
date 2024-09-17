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
    """Install a Python package using pip."""
    print(f"Installing {package} library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
except ImportError:
    install_package("requests")
    import requests

def get_remote_sha256(url: str) -> str:
    """Fetch the SHA256 hash of a remote file."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text.strip()  # Return the hash as a string
    except requests.RequestException as e:
        print(f"Warning: Failed to get remote SHA256. Error: {e}")
        return None

def calculate_sha256(file_path: str) -> str:
    """Calculate the SHA256 hash of a local file."""
    sha256_hash = hashlib.sha256()  # Create a new SHA256 hash object
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):  # Read the file in chunks
            sha256_hash.update(byte_block)  # Update the hash with the chunk
    return sha256_hash.hexdigest()  # Return the hex representation of the hash

def download_file(url: str, local_path: str) -> None:
    """Download a file from a URL to a local path."""
    response = requests.get(url, stream=True)  # Stream the download
    total_size = int(response.headers.get('content-length', 0))  # Get total size
    block_size = 8192  # Size of each chunk to read
    downloaded_size = 0  # Track downloaded size

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:  # If chunk is not empty
                f.write(chunk)  # Write chunk to file
                downloaded_size += len(chunk)  # Update downloaded size
                percent = int(50 * downloaded_size / total_size)  # Calculate progress
                sys.stdout.write(f"\r[{'=' * percent}{' ' * (50-percent)}] {downloaded_size}/{total_size} bytes")
                sys.stdout.flush()  # Flush the output buffer
    print("\nDownload completed.")

def verify_download(file_path: str) -> None:
    """Verify the downloaded file's integrity using SHA256."""
    print("Verifying download...")
    remote_sha256 = get_remote_sha256(FFMPEG_SHA256_URL)  # Get the expected hash

    if remote_sha256 is None:
        print("Skipping hash verification due to unavailable remote SHA256.")
        return

    local_sha256 = calculate_sha256(file_path)  # Calculate local hash

    print(f"Remote SHA256: {remote_sha256}")
    print(f"Local SHA256:  {local_sha256}")

    if remote_sha256 != local_sha256:  # Compare hashes
        raise ValueError("Downloaded file hash does not match the expected hash.")
    print("Hash verification successful.")

def download_7zip() -> str:
    """Download the 7-Zip executable if it doesn't exist."""
    seven_zip_path = os.path.join(ASSETS_DIR, "7zr.exe")  # Path for 7-Zip
    if not os.path.exists(seven_zip_path):  # Check if it already exists
        print("Downloading 7-Zip standalone executable...")
        download_file(SEVEN_ZIP_URL, seven_zip_path)  # Download 7-Zip
    return seven_zip_path  # Return the path to the executable

def extract_ffmpeg(seven_zip_path: str, file_path: str) -> None:
    """Extract the FFmpeg files from the downloaded archive."""
    print("Extracting FFmpeg...")

    # Extract the folder name from the downloaded 7z file
    cmd = [seven_zip_path, "l", file_path]  # List the contents of the archive
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # Execute the command
    # Parse the output to find folder names (assuming they are the first part of the line)
    folder_names = [line.split()[0] for line in result.stdout.splitlines() if line and not line.startswith('---')]  # Get folder names

    if not folder_names:  # Check if any folder names were found
        raise ValueError("No directory found in the extracted archive.")

    extracted_folder_name = folder_names[0]  # Get the first folder name
    extracted_path = os.path.join(ASSETS_DIR, extracted_folder_name)  # Use the extracted folder name

    # Run the 7-Zip command to extract the files
    cmd = [seven_zip_path, "x", file_path, f"-o{ASSETS_DIR}", "-y"]
    subprocess.run(cmd, check=True, capture_output=True)  # Execute the command
    print("Extraction completed.")

    # The expected extracted path is now directly the ASSETS_DIR
    final_path = os.path.join(ASSETS_DIR, FFMPEG_DIR)  # Final path for FFmpeg

    if os.path.exists(final_path):  # If the final path exists, remove it
        shutil.rmtree(final_path)

    # Check if the extracted path exists before renaming
    if not os.path.exists(extracted_path):
        raise FileNotFoundError(f"Extracted path does not exist: {extracted_path}")

    os.rename(extracted_path, final_path)  # Rename the extracted folder
    print(f"Renamed extracted directory to {FFMPEG_DIR}")

    os.remove(file_path)  # Remove the downloaded archive

def test_ffmpeg(ffmpeg_path: str, ffprobe_path: str) -> None:
    """Test if FFmpeg and FFprobe are working by checking their versions."""
    for exe_path, name in [(ffmpeg_path, "FFmpeg"), (ffprobe_path, "FFprobe")]:
        try:
            result = subprocess.run([exe_path, "-version"], capture_output=True, text=True, check=True)
            version_line = result.stdout.split('\n')[0]  # Get the first line of output
            print(f"{name} version: {version_line}")  # Print the version
        except subprocess.CalledProcessError as e:
            print(f"Error running {name}: {e}")
            print(f"stderr: {e.stderr}")  # Print any error messages
            raise

def ensure_ffmpeg_installed() -> Tuple[str, str]:
    """Ensure that FFmpeg and FFprobe are installed and return their paths."""
    ffmpeg_path = os.path.join(ASSETS_DIR, FFMPEG_DIR, "bin", "ffmpeg.exe")  # Path to FFmpeg
    ffprobe_path = os.path.join(ASSETS_DIR, FFMPEG_DIR, "bin", "ffprobe.exe")  # Path to FFprobe

    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):  # Check if both executables exist
        print("FFmpeg is already installed.")
    else:
        print("FFmpeg not found. Downloading...")
        os.makedirs(ASSETS_DIR, exist_ok=True)  # Create assets directory if it doesn't exist
        file_path = os.path.join(ASSETS_DIR, "ffmpeg.7z")  # Path for the downloaded archive

        try:
            download_file(FFMPEG_URL, file_path)  # Download FFmpeg
            print(f"Download completed. File size: {os.path.getsize(file_path)} bytes")

            verify_download(file_path)  # Verify the downloaded file
            seven_zip_path = download_7zip()  # Ensure 7-Zip is available
            extract_ffmpeg(seven_zip_path, file_path)  # Extract FFmpeg files

            print("FFmpeg installation completed.")
        except Exception as e:
            print(f"Error during FFmpeg installation: {e}")
            if os.path.exists(file_path):  # Clean up if there's an error
                os.remove(file_path)
            raise

    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):  # Check if executables are still missing
        raise FileNotFoundError(f"FFmpeg or FFprobe executable not found at expected paths:\nffmpeg: {ffmpeg_path}\nffprobe: {ffprobe_path}")

    test_ffmpeg(ffmpeg_path, ffprobe_path)  # Test the executables

    return ffmpeg_path, ffprobe_path  # Return the paths to the executables