import os
import json
import subprocess
import concurrent.futures
from typing import List, Tuple
from file_utils import estimate_scale_factor

def get_image_info(ffprobe_path: str, input_file: str, verbose: bool) -> Tuple[int, int, int]:
    """Get information about an image file using FFprobe."""
    # Suppress the verbose output for getting info
    # if verbose:
    #     print(f"Getting info for {input_file}...")  # Verbose output for debugging
    cmd = [
        ffprobe_path,
        "-v", "quiet",  # Suppress unnecessary output
        "-print_format", "json",  # Output in JSON format
        "-show_format",  # Show format information
        "-show_streams",  # Show stream information
        input_file  # The input image file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)  # Run the command
    data = json.loads(result.stdout)  # Parse the JSON output

    # Extract width, height, and size from the parsed data
    width = int(data['streams'][0]['width'])
    height = int(data['streams'][0]['height'])
    size = int(data['format']['size'])

    return width, height, size  # Return the extracted information

def process_file_sizes(input_folder: str, target_size: int, verbose: bool) -> List[str]:
    """Check file sizes and return a list of files that need processing."""
    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    files_to_process = []  # List to store files that need processing

    for file in image_files:
        try:
            current_size = os.path.getsize(file)  # Get the current size of the file
        except OSError as e:
            print(f"Error accessing {file}: {e}")  # Log the error
            current_size = 0  # Set current_size to 0 if there's an error
            continue  # Skip this file if there's an error

        if current_size > target_size:  # Only add files that exceed the target size
            files_to_process.append(file)
        elif verbose:
            print(f"Skipping {file}: current size {current_size} bytes is within target size {target_size} bytes.")

    if verbose:
        print(f"\nFiles to process: {len(files_to_process)} out of {len(image_files)} total files.")  # Summary of files to process

    return files_to_process  # Return the list of files that need processing

def process_file(ffprobe_path: str, input_file: str, target_size: int, verbose: bool) -> Tuple[str, Tuple[int, int], str, int]:
    """Process a single image file to determine its dimensions based on target file size."""
    # Get the current size of the file
    current_size = os.path.getsize(input_file)

    # Check if the current size is already within the target size limit
    if current_size <= target_size:
        if verbose:
            print(f"Skipping {input_file}: current size {current_size} bytes is within target size {target_size} bytes.")
        return input_file, (0, 0), os.path.join("out", f"resized_{os.path.basename(input_file)}"), target_size  # Return without processing

    # Get image info to calculate new dimensions
    width, height, _ = get_image_info(ffprobe_path, input_file, verbose)  # Get image info

    # Set initial dimensions
    initial_width = int(width * .95)
    initial_height = int(height * .95)

    # Calculate the target dimensions based on the target file size
    target_bytes = target_size

    # Return the initial dimensions for resizing
    output_file = os.path.join("out", f"resized_{os.path.basename(input_file)}")  # Define output file path

    return input_file, (initial_width, initial_height), output_file, target_size  # Return input file, initial dimensions, output file path, and target size

def probe(ffprobe_path: str, files_to_process: List[str], target_size: int, verbose: bool) -> List[Tuple[str, Tuple[int, int], str, int]]:
    """Probe all image files that need processing to determine their resizing parameters."""
    results = []  # Initialize a list to store results

    for file in files_to_process:
        if verbose:
            print(f"Getting info for {file}...")  # Verbose output for debugging
        width, height, _ = get_image_info(ffprobe_path, file, verbose)  # Get image info
        current_size = os.path.getsize(file)  # Get current size
        scale_factor = estimate_scale_factor(current_size, target_size)  # Calculate scale factor
        output_file = os.path.join("out", f"resized_{os.path.basename(file)}")  # Define output file path

        # Calculate new dimensions based on scale factor
        new_dimensions = (int(width * scale_factor), int(height * scale_factor))

        if verbose:
            print(f"Processing {file}:")
            print(f"  Current size: {current_size} bytes")  # Log current size
            print(f"  Target size: {target_size} bytes")  # Log target size
            print(f"  Scale factor = {scale_factor}")  # Log scale factor
            print(f"  Output = {output_file}")  # Verbose output

        results.append((file, new_dimensions, output_file, target_size))  # Append results

    return results  # Return the list of results

def resize_image(ffmpeg_path: str, input_file: str, output_file: str, new_dimensions: Tuple[int, int], target_size: int, verbose: bool) -> Tuple[str, int, int, float, int]:
    """Resize the image to the target size."""
    # Validate dimensions
    if new_dimensions[0] <= 0 or new_dimensions[1] <= 0:
        print(f"Invalid dimensions {new_dimensions} for {input_file}. Skipping resizing.")
        return output_file, os.path.getsize(input_file), os.path.getsize(output_file), 0, 0  # Return without resizing

    cmd = [
        ffmpeg_path,
        "-i", input_file,
        "-vf", f"scale={new_dimensions[0]}:{new_dimensions[1]}",
        "-y",
        output_file
    ]
    if verbose:
        print(f"Resizing {input_file} to {output_file} with dimensions {new_dimensions}...")

    subprocess.run(cmd, check=True, capture_output=True)

    initial_size = os.path.getsize(input_file)
    final_size = os.path.getsize(output_file)
    compression_ratio = initial_size / final_size if final_size != 0 else 0
    iteration_count = 1  # Initialize iteration count

    # Adjust the weight difference calculation
    weight_difference = abs(initial_size - target_size)
    adjustment_factor = 0.9  # Factor to reduce the weight difference impact
    new_dimensions = (
        int(new_dimensions[0] * (1 - adjustment_factor * (weight_difference / initial_size))),
        int(new_dimensions[1] * (1 - adjustment_factor * (weight_difference / initial_size)))
    )

    # Print the number of iterations
    print(f"Iteration {iteration_count}: Resized {input_file} to {output_file} with dimensions {new_dimensions}.")

    return output_file, initial_size, final_size, compression_ratio, iteration_count

def process_images(ffmpeg_path: str, probe_results: List[Tuple[str, Tuple[int, int], str, int]], verbose: bool) -> None:
    """Process all images by resizing them based on the probe results."""
    os.makedirs("out", exist_ok=True)  # Ensure the output directory exists
    compression_data = []  # List to store compression results

    with concurrent.futures.ThreadPoolExecutor() as executor:  # Use a thread pool for parallel processing
        # Submit tasks to resize each image
        futures = [executor.submit(resize_image, ffmpeg_path, input_file, output_file, new_dimensions, target_size, verbose)
                   for input_file, new_dimensions, output_file, target_size in probe_results]  # Include target_size

        for future in concurrent.futures.as_completed(futures):
            output_file, initial_size, final_size, compression_ratio, iteration_count = future.result()  # Get results
            compression_data.append((os.path.basename(output_file), initial_size, final_size, compression_ratio, iteration_count))  # Store results

    # Print summary of compression results
    print("\nCompression Summary:")
    for file_name, initial_size, final_size, compression_ratio, iteration_count in compression_data:
        print(f"{file_name}: Initial size: {initial_size} bytes, Final size: {final_size} bytes, Compression ratio: {compression_ratio:.2f}, Iterations: {iteration_count}")

    print("Image processing completed.")  # Indicate completion