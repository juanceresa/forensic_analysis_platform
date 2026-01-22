"""Tests for binarize module."""

import pytest
import numpy as np
import cv2


def test_sauvola_threshold():
    """Test Sauvola adaptive thresholding."""
    # Create image with varying background
    image = np.ones((100, 100), dtype=np.uint8) * 200
    # Add dark text regions
    image[20:30, 20:80] = 50  # Dark text
    image[50:60, 20:80] = 50  # More dark text
    # Add gradient background
    for i in range(100):
        image[70:80, i] = 180 + i // 5

    from farmer_factory.prepare.binarize import sauvola_threshold
    binary = sauvola_threshold(image)

    # Check output is binary (only 0 and 255)
    unique_vals = np.unique(binary)
    assert len(unique_vals) <= 2
    assert 0 in unique_vals or 255 in unique_vals

    # Check dimensions preserved
    assert binary.shape == image.shape
