"""Deskew module for image rotation correction."""

import cv2
import numpy as np


def detect_skew_angle(image: np.ndarray) -> float:
    """
    Detect skew angle of document using Hough line detection.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Skew angle in degrees (positive = clockwise rotation needed)
    """
    # Binarize image
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Edge detection
    edges = cv2.Canny(binary, 50, 150, apertureSize=3)

    # Detect lines using Hough transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    if lines is None or len(lines) == 0:
        return 0.0  # No lines detected, assume straight

    # Extract angles from detected lines
    angles = []
    for line in lines:
        rho, theta = line[0]
        # Convert theta to degrees
        # Negative sign to match OpenCV rotation convention
        angle_deg = 90.0 - np.degrees(theta)

        # Filter to horizontal-ish lines (within ±45 degrees of horizontal)
        if abs(angle_deg) < 45:
            angles.append(angle_deg)

    if len(angles) == 0:
        return 0.0

    # Return median angle (robust to outliers)
    return np.median(angles)


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotate image to correct skew.

    Args:
        image: Grayscale image (H x W)
        angle: Rotation angle in degrees (positive = clockwise)

    Returns:
        Rotated image with same dimensions
    """
    h, w = image.shape[:2]
    center = (w / 2, h / 2)

    # Get rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Rotate with white background
    rotated = cv2.warpAffine(
        image,
        rotation_matrix,
        (w, h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255
    )

    return rotated
