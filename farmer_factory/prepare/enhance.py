"""Enhancement module for contrast and lighting correction."""

import cv2
import numpy as np


def apply_clahe(image: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

    Args:
        image: Grayscale image (H x W)

    Returns:
        Enhanced image with improved local contrast
    """
    # Create CLAHE object with clipLimit=2.0 and tileGridSize=(8, 8)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)


def correct_lighting(image: np.ndarray) -> np.ndarray:
    """
    Correct uneven lighting using morphological background estimation.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Image with corrected lighting
    """
    # Estimate background using morphological opening with large kernel
    kernel_size = max(image.shape[0] // 10, image.shape[1] // 10)
    if kernel_size % 2 == 0:
        kernel_size += 1  # Ensure odd
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # Background estimation
    background = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

    # Subtract background and normalize
    corrected = cv2.subtract(image, background)

    # Rescale to full range
    corrected = cv2.normalize(corrected, None, 0, 255, cv2.NORM_MINMAX)

    return corrected


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Full enhancement pipeline: lighting correction + CLAHE.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Enhanced image
    """
    # Correct lighting first
    corrected = correct_lighting(image)

    # Apply CLAHE for local contrast
    enhanced = apply_clahe(corrected)

    return enhanced
