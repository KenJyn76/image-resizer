# Image Resizer

## Overview
The Image Resizer project is a command-line tool designed to resize images to a target file size using FFmpeg. It processes images in a specified folder, ensuring they meet the desired size criteria.

## Features
- Resize images to a specified target size (e.g., '500K', '5M', '2G').
- Probe images without modifying them.
- Verbose output for detailed processing information.
- Automatic installation and verification of FFmpeg.

## Requirements
- Python 3.x
- FFmpeg (automatically installed if not present)

## Installation
1. Clone the repository:
   ```sh
   git clone <repository_url>
   cd image-resizer
   ```

2. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
Run the main script with the required arguments:
```sh
python main.py <input_folder> <target_size> [-v] [--probe-only]
```

### Arguments
- `input_folder`: Folder containing images to resize.
- `target_size`: Target file size (e.g., '500K', '5M', '2G').
- `-v`, `--verbose`: Enable verbose output.
- `--probe-only`: Perform a probe without modifying files.

### Example
```sh
python main.py "C:\Users\Admin\Pictures\Camera Roll - Copy" 2M -v
```

## Code Structure
- `main.py`: Entry point of the application. Handles command-line arguments and initiates image processing.
  ```python:main.py
  startLine: 1
  endLine: 31
  ```

- `ffmpeg_utils.py`: Utilities for ensuring FFmpeg is installed and functional.
  ```python:ffmpeg_utils.py
  startLine: 1
  endLine: 167
  ```

- `.gitignore`: Specifies files and directories to be ignored by Git.
  ```plaintext:.gitignore
  startLine: 1
  endLine: 4
  ```

## Error Handling
- The script checks if the `target_size` is valid and raises a `ValueError` if it is `None`.
- FFmpeg installation errors are caught and reported, with cleanup of partially downloaded files.

## Contributing
Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.
```
