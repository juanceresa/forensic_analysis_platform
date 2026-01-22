"""Tests for pipeline module."""

import pytest
import numpy as np
from farmer_factory.prepare.triage import DocumentPath


def test_processed_page_creation():
    """Test ProcessedPage dataclass creation."""
    from farmer_factory.prepare.pipeline import ProcessedPage

    # Create test image
    test_image = np.ones((100, 100), dtype=np.uint8) * 255

    page = ProcessedPage(
        image=test_image,
        path=DocumentPath.TYPED,
        metadata={
            "skew_angle": 2.5,
            "triage_confidence": 0.85,
        }
    )

    assert page.path == DocumentPath.TYPED
    assert page.metadata["skew_angle"] == 2.5
    assert page.image.shape == (100, 100)


def test_preprocessing_pipeline_creation():
    """Test PreprocessingPipeline instantiation."""
    from farmer_factory.prepare.pipeline import PreprocessingPipeline

    pipeline = PreprocessingPipeline()

    # Just check it creates successfully
    assert pipeline is not None


def test_process_page_typed():
    """Test processing a typed document page."""
    from farmer_factory.prepare.pipeline import PreprocessingPipeline
    import cv2

    # Create synthetic typed document
    image = np.ones((200, 200), dtype=np.uint8) * 230
    # Add regular horizontal lines (typed text)
    for y in range(20, 180, 15):
        image[y:y+5, 20:180] = 60

    # Add slight rotation
    center = (100, 100)
    rotation_matrix = cv2.getRotationMatrix2D(center, 3.0, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (200, 200),
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=255)

    pipeline = PreprocessingPipeline()
    result = pipeline.process_page(rotated)

    # Check result
    assert result.path == DocumentPath.TYPED
    assert result.image.shape == rotated.shape
    assert "skew_angle" in result.metadata
    assert "triage_confidence" in result.metadata


def test_process_page_handwritten():
    """Test processing a handwritten document page."""
    from farmer_factory.prepare.pipeline import PreprocessingPipeline

    # Create synthetic handwritten document
    image = np.ones((200, 200), dtype=np.uint8) * 220
    # Add irregular lines (handwriting)
    y_positions = [20, 40, 65, 85, 110, 135, 160]
    for y in y_positions:
        thickness = np.random.randint(2, 4)
        start_x = np.random.randint(10, 20)
        end_x = np.random.randint(170, 190)
        image[y:y+thickness, start_x:end_x] = np.random.randint(40, 80)

    pipeline = PreprocessingPipeline()
    result = pipeline.process_page(image)

    # Check result
    assert result.path == DocumentPath.HANDWRITTEN
    assert result.image.shape == image.shape
    assert "skew_angle" in result.metadata
