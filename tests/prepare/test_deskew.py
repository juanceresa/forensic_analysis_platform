"""Tests for deskew module."""

import pytest
import numpy as np
import cv2


def test_detect_skew_angle_straight():
    """Test skew detection on straight document."""
    # Create straight horizontal lines
    image = np.ones((200, 200), dtype=np.uint8) * 255
    for y in range(50, 150, 20):
        image[y:y+2, 20:180] = 0

    from farmer_factory.prepare.deskew import detect_skew_angle
    angle = detect_skew_angle(image)

    assert abs(angle) < 1.0  # Should be near 0 degrees


def test_detect_skew_angle_rotated():
    """Test skew detection on rotated document."""
    # Create horizontal lines
    image = np.ones((200, 200), dtype=np.uint8) * 255
    for y in range(50, 150, 20):
        image[y:y+2, 20:180] = 0

    # Rotate by 5 degrees
    center = (100, 100)
    rotation_matrix = cv2.getRotationMatrix2D(center, 5.0, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (200, 200),
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=255)

    from farmer_factory.prepare.deskew import detect_skew_angle
    angle = detect_skew_angle(rotated)

    # Should detect rotation close to 5 degrees
    assert 4.0 < angle < 6.0
