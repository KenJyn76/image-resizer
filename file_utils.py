import re
import argparse

def estimate_scale_factor(current_size: int, target_size: int) -> float:
    """Estimate the scale factor to resize an image based on current and target sizes."""
    if current_size <= 0:
        raise ValueError("Current size must be greater than zero.")
    return (target_size / current_size) ** 0.5  # Calculate the scale factor

def parse_size(size_str: str) -> int:
    """Convert a string like '500M' or '12G' to bytes."""
    match = re.match(r'^(\d*\.?\d+)\s*([KMGT]?)B?$', size_str, re.I)
    if not match:
        raise argparse.ArgumentTypeError("Invalid size format. Use something like '500M' or '12G'.")

    number, unit = match.groups()
    number = float(number)  # Convert the number part to float
    unit = unit.upper()  # Normalize the unit to uppercase

    # Define multipliers for each unit
    multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
    size_in_bytes = int(number * multipliers.get(unit, 1))  # Return the size in bytes

    if size_in_bytes <= 0:  # Ensure target size is not zero or negative
        raise ValueError("Target size must be greater than zero.")

    print(f"Parsed target size: {size_str} -> {size_in_bytes} bytes")  # Log the parsed size
    return size_in_bytes