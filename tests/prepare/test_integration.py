"""Integration tests for preprocessing pipeline."""

import pytest
import numpy as np
import cv2
from farmer_factory.prepare import PreprocessingPipeline, DocumentPath


def test_full_pipeline_typed_document():
    """Test full pipeline on synthetic typed document."""
    # Create realistic typed document: regular lines, slight skew, noise
    image = np.ones((400, 600), dtype=np.uint8) * 235

    # Add regular typed text lines
    for y in range(40, 360, 25):
        # Simulate text blocks
        image[y:y+12, 50:550] = np.random.randint(40, 80, (12, 500))

    # Add noise
    noise = np.random.randint(-10, 10, image.shape, dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Add rotation
    center = (300, 200)
    rotation_matrix = cv2.getRotationMatrix2D(center, 2.5, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (600, 400),
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=255)

    # Process through pipeline
    pipeline = PreprocessingPipeline()
    result = pipeline.process_page(rotated)

    # Assertions
    assert result.path == DocumentPath.TYPED
    assert result.image.shape == rotated.shape
    assert result.metadata["triage_confidence"] > 0.1

    # TYPED path should be binary
    unique_vals = np.unique(result.image)
    assert len(unique_vals) <= 2  # Only 0 and 255

    # Should have detected skew
    assert "skew_angle" in result.metadata
    assert abs(result.metadata["skew_angle"]) < 10.0  # Reasonable angle


def test_full_pipeline_handwritten_document():
    """Test full pipeline on synthetic handwritten document."""
    # Create realistic handwritten document: irregular lines, varying intensity
    image = np.ones((400, 600), dtype=np.uint8) * 220

    # Add irregular handwritten lines
    y_positions = [40, 70, 105, 135, 170, 210, 245, 280, 320, 360]
    for y in y_positions:
        thickness = np.random.randint(3, 8)
        start_x = np.random.randint(40, 60)
        end_x = np.random.randint(530, 580)
        intensity = np.random.randint(30, 90)
        image[y:y+thickness, start_x:end_x] = intensity

    # Process through pipeline
    pipeline = PreprocessingPipeline()
    result = pipeline.process_page(image)

    # Assertions
    assert result.path == DocumentPath.HANDWRITTEN
    assert result.image.shape == image.shape

    # HANDWRITTEN path should stay grayscale
    unique_vals = np.unique(result.image)
    assert len(unique_vals) > 2  # Not binary

    # Should have metadata
    assert "skew_angle" in result.metadata
    assert "triage_confidence" in result.metadata


def test_pipeline_preserves_dimensions():
    """Test that pipeline preserves image dimensions."""
    test_sizes = [
        (200, 300),
        (400, 600),
        (100, 100),
    ]

    pipeline = PreprocessingPipeline()

    for h, w in test_sizes:
        image = np.ones((h, w), dtype=np.uint8) * 200
        result = pipeline.process_page(image)
        assert result.image.shape == (h, w)
