import re
import argparse

def estimate_scale_factor(current_size: int, target_size: int) -> float:
    return (target_size / current_size) ** 0.5

def parse_size(size_str: str) -> int:
    """Convert a string like '500M' or '12G' to bytes."""
    match = re.match(r'^(\d*\.?\d+)\s*([KMGT]?)B?$', size_str, re.I)
    if not match:
        raise argparse.ArgumentTypeError("Invalid size format. Use something like '500M' or '12G'.")

    number, unit = match.groups()
    number = float(number)
    unit = unit.upper()

    multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
    return int(number * multipliers.get(unit, 1))