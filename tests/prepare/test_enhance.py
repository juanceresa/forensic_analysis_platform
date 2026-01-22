"""Tests for enhance module."""

import pytest
import numpy as np
import cv2


def test_apply_clahe():
    """Test CLAHE contrast enhancement."""
    # Create low-contrast image
    low_contrast = np.ones((100, 100), dtype=np.uint8) * 120
    # Add some variation
    low_contrast[30:70, 30:70] = 140

    from farmer_factory.prepare.enhance import apply_clahe
    enhanced = apply_clahe(low_contrast)

    # Check contrast improved (higher standard deviation)
    assert np.std(enhanced) > np.std(low_contrast)
    # Check dimensions preserved
    assert enhanced.shape == low_contrast.shape


def test_correct_lighting():
    """Test lighting correction for uneven illumination."""
    # Create image with gradient (uneven lighting)
    image = np.zeros((100, 100), dtype=np.uint8)
    for i in range(100):
        image[:, i] = int(100 + i * 1.5)  # Gradient from 100 to 250

    from farmer_factory.prepare.enhance import correct_lighting
    corrected = correct_lighting(image)

    # Check lighting is more uniform (lower std)
    col_means = np.mean(corrected, axis=0)
    assert np.std(col_means) < np.std(np.mean(image, axis=0))
    # Check dimensions preserved
    assert corrected.shape == image.shape


def test_enhance_image():
    """Test full enhancement pipeline."""
    # Create faded, low-contrast image
    image = np.ones((100, 100), dtype=np.uint8) * 100
    image[20:80, 20:80] = 120

    from farmer_factory.prepare.enhance import enhance_image
    enhanced = enhance_image(image)

    # Just check it runs and returns valid image
    assert enhanced.shape == image.shape
    assert enhanced.dtype == np.uint8
