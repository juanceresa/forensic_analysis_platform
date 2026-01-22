"""Binarization module for converting to black and white."""

import cv2
import numpy as np


def sauvola_threshold(image: np.ndarray, window_size: int = 25, k: float = 0.2) -> np.ndarray:
    """
    Apply Sauvola adaptive thresholding.

    Args:
        image: Grayscale image (H x W)
        window_size: Local window size (odd number)
        k: Sauvola parameter (0.2-0.5, lower = more aggressive)

    Returns:
        Binary image (0 = black/text, 255 = white/background)
    """
    # Ensure window size is odd
    if window_size % 2 == 0:
        window_size += 1

    # Convert to float for calculations
    img_float = image.astype(np.float64)

    # Compute local mean using box filter
    mean = cv2.boxFilter(img_float, ddepth=-1, ksize=(window_size, window_size))

    # Compute local standard deviation
    mean_sq = cv2.boxFilter(img_float ** 2, ddepth=-1, ksize=(window_size, window_size))
    variance = mean_sq - mean ** 2
    std = np.sqrt(np.maximum(variance, 0))

    # Sauvola threshold formula
    # T(x,y) = mean(x,y) * (1 + k * (std(x,y) / R - 1))
    # where R is the dynamic range of std (typically 128 for 8-bit images)
    R = 128.0
    threshold = mean * (1 + k * (std / R - 1))

    # Apply threshold
    binary = np.where(img_float > threshold, 255, 0).astype(np.uint8)

    return binary
